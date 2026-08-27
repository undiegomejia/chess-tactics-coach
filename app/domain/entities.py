class EvaluationEntityResponse:
    fen: str
    evaluation: "EvaluationEntity"

class EvaluationEntity:
    type: str
    value: int