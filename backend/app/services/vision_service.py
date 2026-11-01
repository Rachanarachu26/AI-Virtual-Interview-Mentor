"""Non-verbal analysis using MediaPipe Holistic + OpenCV.

MediaPipe DETECTS landmarks/features. This module DERIVES interview-relevant
behavioural metrics (eye contact, posture, head stability, gestures) from those
landmarks. MediaPipe itself does not produce the final interview score.

The whole module is defensive: if MediaPipe/OpenCV is unavailable or no face is
detected, `available` is returned False and the interview continues normally.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("vision_service")

_holistic = None
_vision_failed = False


def _get_holistic():
    """Lazy-init a single MediaPipe Holistic instance."""
    global _holistic, _vision_failed
    if _holistic is not None:
        return _holistic
    if _vision_failed:
        return None
    try:
        import mediapipe as mp  # imported lazily

        _holistic = mp.solutions.holistic.Holistic(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            refine_face_landmarks=True,
        )
        return _holistic
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.error("Failed to init MediaPipe Holistic: %s", exc)
        _vision_failed = True
        return None


def _decode_image(frame_bytes: bytes):
    import cv2
    import numpy as np

    arr = np.frombuffer(frame_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def analyze_frames(frames: List[bytes]) -> Dict:
    """Analyse a list of image frames (JPEG/PNG bytes) and return metrics.

    Returns a dict shaped like the VisionMetric model. Never raises.
    """
    unavailable = {
        "available": False,
        "eye_contact_percentage": 0.0,
        "posture_score": 0.0,
        "head_movement_score": 0.0,
        "gesture_score": 0.0,
        "frames_analyzed": 0,
    }

    if not frames:
        return unavailable

    holistic = _get_holistic()
    if holistic is None:
        return unavailable

    try:
        import cv2
    except Exception as exc:
        logger.error("OpenCV unavailable: %s", exc)
        return unavailable

    nose_positions: List[tuple] = []
    eye_contact_hits = 0
    posture_scores: List[float] = []
    hands_detected_frames = 0
    hand_positions: List[tuple] = []
    frames_analyzed = 0

    for fb in frames:
        img = _decode_image(fb)
        if img is None:
            continue
        try:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)
        except Exception as exc:
            logger.warning("Holistic.process failed on a frame: %s", exc)
            continue

        face = results.face_landmarks
        pose = results.pose_landmarks
        if face is None and pose is None:
            continue

        frames_analyzed += 1

        # ---- Eye contact & head position (from face landmarks) ----
        if face is not None:
            lm = face.landmark
            # Landmark 1 ~ nose tip, 33 ~ left eye outer, 263 ~ right eye outer.
            nose = lm[1]
            left_eye = lm[33]
            right_eye = lm[263]
            nose_positions.append((nose.x, nose.y))

            # Facing camera: nose x roughly centered between the two eyes.
            eye_mid_x = (left_eye.x + right_eye.x) / 2.0
            horiz_offset = abs(nose.x - eye_mid_x)
            eye_span = abs(right_eye.x - left_eye.x) + 1e-6
            # Small offset relative to eye span => looking at camera.
            if horiz_offset / eye_span < 0.18 and 0.25 < nose.y < 0.75:
                eye_contact_hits += 1

        # ---- Posture (from pose landmarks: shoulders) ----
        if pose is not None:
            plm = pose.landmark
            left_sh = plm[11]
            right_sh = plm[12]
            # Shoulders level => small vertical difference.
            shoulder_tilt = abs(left_sh.y - right_sh.y)
            # Centered => shoulder midpoint near horizontal center.
            mid_x = (left_sh.x + right_sh.x) / 2.0
            centering = abs(mid_x - 0.5)
            posture = 100.0 - (shoulder_tilt * 220.0) - (centering * 120.0)
            posture_scores.append(max(0.0, min(100.0, posture)))

        # ---- Hand gestures ----
        if results.left_hand_landmarks or results.right_hand_landmarks:
            hands_detected_frames += 1
            hand = results.right_hand_landmarks or results.left_hand_landmarks
            wrist = hand.landmark[0]
            hand_positions.append((wrist.x, wrist.y))

    if frames_analyzed == 0:
        return unavailable

    # Eye contact percentage.
    eye_contact_pct = round((eye_contact_hits / frames_analyzed) * 100, 1)

    # Head movement: lower positional variance => higher stability score.
    head_stability = _stability_score(nose_positions)

    # Posture: average of per-frame posture scores.
    posture_score = round(sum(posture_scores) / len(posture_scores), 1) if posture_scores else 0.0

    # Gestures: reward natural presence & movement, penalise none or excessive.
    gesture_score = _gesture_score(hands_detected_frames, frames_analyzed, hand_positions)

    return {
        "available": True,
        "eye_contact_percentage": eye_contact_pct,
        "posture_score": posture_score,
        "head_movement_score": head_stability,
        "gesture_score": gesture_score,
        "frames_analyzed": frames_analyzed,
    }


def _variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _stability_score(positions: List[tuple]) -> float:
    """Map positional variance of the nose to a 0-100 stability score."""
    if len(positions) < 2:
        return 70.0  # neutral when we can't measure movement
    var_x = _variance([p[0] for p in positions])
    var_y = _variance([p[1] for p in positions])
    movement = (var_x + var_y) ** 0.5
    # movement ~0 => very stable (100); larger => lower.
    score = 100.0 - movement * 900.0
    return round(max(0.0, min(100.0, score)), 1)


def _gesture_score(hand_frames: int, total_frames: int, positions: List[tuple]) -> float:
    """Score gestures: some hand presence & movement is natural; none/too much is worse."""
    if total_frames == 0:
        return 0.0
    presence = hand_frames / total_frames

    if presence < 0.1:
        base = 55.0  # very limited gestures
    elif presence <= 0.7:
        base = 90.0  # natural
    else:
        base = 70.0  # possibly excessive

    # A little movement of the hands reads as natural engagement.
    move = (_variance([p[0] for p in positions]) + _variance([p[1] for p in positions])) ** 0.5
    if 0.005 < move < 0.15:
        base += 8.0
    return round(max(0.0, min(100.0, base)), 1)


def analyze_single_frame(frame_bytes: bytes) -> Optional[Dict]:
    """Convenience helper for analysing a single frame."""
    return analyze_frames([frame_bytes])
