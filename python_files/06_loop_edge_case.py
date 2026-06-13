def print_top_scores(score_list: list) -> None:
    """
    Iterates through the provided list and prints each score.
    """
    for i in range(len(score_list)):
        current_score = score_list[i]
        print(f"Score {i}: {current_score}")