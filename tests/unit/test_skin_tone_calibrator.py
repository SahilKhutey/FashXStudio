from fashx.profile.calibration.skin_tone import SkinToneCalibrator


def test_skin_tone_calibrator_light_monk_scale() -> None:
    # Near Monk 02: (243, 231, 219)
    res = SkinToneCalibrator.calibrate_from_rgb(240, 230, 215)
    assert res.monk_scale_index in (1, 2, 3)
    assert res.hex_code.startswith("#")


def test_skin_tone_calibrator_medium_warm() -> None:
    # Near Monk 06: (160, 126, 86) with high G-B (warm undertone)
    res = SkinToneCalibrator.calibrate_from_rgb(165, 130, 90)
    assert res.monk_scale_index in (5, 6, 7)
    # G=130, B=90 -> G-B=40 > 14 -> warm
    assert res.undertone == "warm"


def test_skin_tone_calibrator_deep_cool() -> None:
    # Deep skin tone, cool undertone (G-B < 5)
    res = SkinToneCalibrator.calibrate_from_rgb(95, 62, 60)
    assert res.monk_scale_index in (7, 8, 9)
    # G=62, B=60 -> G-B=2 < 5 -> cool
    assert res.undertone == "cool"
