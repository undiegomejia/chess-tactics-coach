def eval_distance_to_quality(student_eval_cp: int, target_eval_cp: int, side_to_move: str) -> int:
    """
    Calculate the distance between the student's evaluation and the target evaluation.
    
    Args:
        student_eval_cp (int): The student's evaluation in centipawns.
        target_eval_cp (int): The target evaluation in centipawns.
        side_to_move (str): The side to move, either "white" or "black".
    
    Returns:
        int: The distance to quality_of_response. Positive if the student's evaluation is better than the target,
             negative if worse, and zero if equal.
    """
    # Adjust the sign of the evaluations based on the side to move
    quality_of_response = 0

    if side_to_move == "black":
        student_eval_cp = -student_eval_cp
        target_eval_cp = -target_eval_cp
    # Calculate the distance to quality
    min_distance = max(0, target_eval_cp - student_eval_cp) # Distance is positive if the student's evaluation is better than the target, negative if worse, and zero if equal.
    # shortfall_map with 0–5 quality with boundaries in centipawns ~10/50/100cp
    shortfall_map = {
        5: 10,
        4: 50,
        3: 100,
        2: 150,
        1: 200,
        0: 250,
    }
    for quality, boundary in shortfall_map.items():
       if min_distance <= boundary:
            quality_of_response = quality
            break
        
    return quality_of_response

def apply_sm2(quality: int, repetition_count: int, ease_factor: float, interval: int) -> tuple[int, float, int]:
    # returns the NEW (repetition_count, ease_factor, interval)
    ease_factor = round(max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)), 2)
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
    return repetition_count, ease_factor, interval
