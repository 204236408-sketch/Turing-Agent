from p5_helpers import make_question


def test_question_generate(auth_client):
    question = make_question(auth_client)
    assert question["id"]
