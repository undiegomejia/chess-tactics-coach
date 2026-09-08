from app.use_cases.drill_use_cases import apply_sm2, eval_distance_to_quality


def test_eval_distance_to_quality():

    ev1 = eval_distance_to_quality(student_eval_cp=250, target_eval_cp=0, side_to_move="white")
    assert ev1 == 5

    ev2 = eval_distance_to_quality(student_eval_cp=-155, target_eval_cp=33, side_to_move="black")
    assert ev2 == 5

    ev3 = eval_distance_to_quality(student_eval_cp=-155, target_eval_cp=33, side_to_move="white")
    assert ev3 == 1

    ev4 = eval_distance_to_quality(student_eval_cp=-44, target_eval_cp=0, side_to_move="black")
    assert ev4 == 5

    ev5 = eval_distance_to_quality(student_eval_cp=-300, target_eval_cp=0, side_to_move="white")
    assert ev5 == 0

    ev6 = eval_distance_to_quality(student_eval_cp=40, target_eval_cp=0, side_to_move="white")
    assert ev6 == 5

    ev7 = eval_distance_to_quality(student_eval_cp=70, target_eval_cp=0, side_to_move="black")
    assert ev7 == 3

    '''
    def apply_sm2(quality: int, repetition_count: int, ease_factor: float, interval: int) -> tuple[int, float, int]:
    # returns the NEW (repetition_count, ease_factor, interval)
    if quality < 3:
        repetition_count = 0
        interval = 1
    else:
        if repetition_count == 0:
            interval = 1
        elif repetition_count == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetition_count += 1
    # Apply the SM-2 algorithm to update the repetition count, ease factor, and interval based on the quality of the response.
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return repetition_count, ease_factor, interval

    '''

def test_apply_sm2():
    # Test case 1: quality < 3
    repetition_count, ease_factor, interval = apply_sm2(quality=2, repetition_count=0, ease_factor=2.5, interval=5)
    assert repetition_count == 0
    assert ease_factor == 2.18
    assert interval == 1

    # Test case 2: quality >= 3, repetition_count = 0
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=1, ease_factor=2.5, interval=5)
    assert repetition_count == 2
    assert ease_factor == 2.5
    assert interval == 6

    # Test case 3: quality >= 3, repetition_count = 1
    repetition_count, ease_factor, interval = apply_sm2(quality=5, repetition_count=1, ease_factor=2.5, interval=6)
    assert repetition_count == 2
    assert ease_factor == 2.6
    assert interval == 6

    # Test case 4: quality >= 3, repetition_count > 1
    repetition_count, ease_factor, interval = apply_sm2(quality=5, repetition_count=2, ease_factor=2.5, interval=6)
    assert repetition_count == 3
    assert ease_factor == 2.6
    assert interval == 16  # interval = round(6 * 2.5)

    # test case 5: quality = 3, repetition_count = 1 round down ease factor
    repetition_count, ease_factor, interval = apply_sm2(quality=3, repetition_count=1, ease_factor=2.5, interval=6)
    assert repetition_count == 2
    assert ease_factor == 2.36
    assert interval == 6

    # test exact 1.3 EF floor actually clamping
    repetition_count, ease_factor, interval = apply_sm2(quality=0, repetition_count=0, ease_factor=1.3, interval=5)
    assert repetition_count == 0
    assert ease_factor == 1.3
    assert interval == 1

    # Add this four-review chain as a test, asserting the final (4, 2.6, 39)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=0, ease_factor=2.5, interval=1)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    repetition_count, ease_factor, interval = apply_sm2(quality=4, repetition_count=repetition_count, ease_factor=ease_factor, interval=interval)
    assert repetition_count == 4
    assert ease_factor == 2.5
    assert interval == 38  # interval = round(15 * 2.5) = 38