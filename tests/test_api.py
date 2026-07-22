from app.main import app
from app.db.session import get_db
from app.models import Vote, Proposal, Participant, AuditLog, User

from datetime import datetime, timedelta

from tests.reserve_db_session import SessionLocal as TestSessionLocal

from fastapi.testclient import TestClient

client = TestClient(app)

# ==== GET TEST DB ====
# =====================

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ==== HELPERS ====
# =================

def _clear_db():
    session = TestSessionLocal()

    session.query(AuditLog).delete()
    session.query(Vote).delete()
    session.query(Participant).delete()
    session.query(Proposal).delete()
    session.query(User).delete()

    session.commit()
    session.close()

def _seed_users():
    session = TestSessionLocal()

    user1 = User()
    user1.id = 1
    user1.name = "Anna"
    user1.email = "anna@test.com"

    user2 = User()
    user2.id = 2
    user2.name = "Bruce"
    user2.email = "bruce@test.com"

    user3 = User()
    user3.id = 3
    user3.name = "Charlie"
    user3.email = "charlie@test.com"

    user4 = User()
    user4.id = 4
    user4.name = "Don"
    user4.email = "don@test.com"

    user5 = User()
    user5.id = 5
    user5.name = "Eddie"
    user5.email = "eddie@test.com"

    session.add_all([user1, user2, user3, user4, user5])
    session.commit()
    session.close()

def _create_proposal():

    # === SETUP PROPOSAL (PAYLOAD) ===
    payload = {
        "title": "Test proposal",
        "description": "Test description",
        "author_id": 1,
        "participant_ids": [1, 2]
    }

    #HTTP-REQUEST
    response = client.post("/proposals", json=payload)

    #GET RESPONSE
    data = response.json()

    return response, data, payload

def _start_voting(proposal_id):

    #PAYLOAD
    payload = {"author_id": 1}

    #HTTP-REQUEST
    response = client.post(f"/proposals/{proposal_id}/start", json=payload)

    #GET RESPONSE
    data = response.json()

    return response, data

# ==== PROPOSAL TESTS ====
# ========================

def test_create_proposal():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #STATUS CODE CHECK
    assert response.status_code == 200

    #RESPONSE DETAILS CHECK
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["author_id"] == payload["author_id"]

    #STATUS CHECK
    assert data["status"] == "draft"

def test_empty_participants():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    # === UNUSUAL SETUP PROPOSAL ===
    payload = {
        "title": "Test proposal",
        "description": "Test description",
        "author_id": 1,
        "participant_ids": []
    }

    #HTTP-REQUEST
    response = client.post("/proposals", json=payload)

    #GET RESPONSE
    data = response.json()

    #STATUS CODE CHECK
    assert response.status_code == 400

    #RESPONSE DETAILS CHECK
    assert data["detail"] == "Participants list is empty"

def test_duplicate_participants():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    # === UNUSUAL SETUP PROPOSAL ===
    payload = {
        "title": "Test proposal",
        "description": "Test description",
        "author_id": 1,
        "participant_ids": [1, 1]
    }

    #HTTP-REQUEST
    response = client.post("/proposals", json=payload)

    #GET RESPONSE
    data = response.json()


    #STATUS CODE CHECK
    assert response.status_code == 400

    #RESPONSE DETAILS CHECK
    assert data["detail"] == "Duplicate participants"

def test_user_not_found():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    # === SETUP PROPOSAL (PAYLOAD) ===
    payload = {
        "title": "Test proposal",
        "description": "Test description",
        "author_id": 999,
        "participant_ids": [1, 2]
    }

    #HTTP-REQUEST
    response = client.post("/proposals", json=payload)

    #GET RESPONSE
    data = response.json()

    #STATUS CODE CHECK
    assert response.status_code == 404

    #RESPONSE DETAILS CHECK
    assert data["detail"] == "User not found"

def test_update_proposal():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #STATUS CODE CHECK
    assert response.status_code == 200

    #STATUS CHECK
    assert data["status"] == "draft"

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    # === UPDATE PROPOSAL ===
    payload_2 = {
        "author_id": 1,
        "title": "UPD",
        "description": "upd"
    }

    #HTTP-REQUEST
    response_2 = client.patch(f"/proposals/{proposal_id}", json=payload_2)

    #GET RESPONSE
    data_2 = response_2.json()

    #STATUS CODE CHECK
    assert response_2.status_code == 200

    #RESPONSE DETAILS CHECK
    assert "id" in data
    assert data_2["title"] == payload_2["title"]
    assert data_2["description"] == payload_2["description"]

def test_update_non_draft_proposal():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    # === UPDATE PROPOSAL ===
    payload = {
        "author_id": 1,
        "title": "UPD",
        "description": "upd"
    }

    #HTTP-REQUEST
    response = client.patch(f"/proposals/{proposal_id}", json=payload)

    #GET RESPONSE
    data_2 = response.json()

    #STATUS CODE CHECK
    assert response.status_code == 409

    #RESPONSE DETAILS CHECK
    assert data_2["detail"] == "Proposal in a wrong state"

def test_delete_already_deleted_proposal():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    # === DELETE PROPOSAL ===
    payload_2 = {"author_id": 1}

    #HTTP-REQUEST
    response_2 = client.request("DELETE", f"/proposals/{proposal_id}", json=payload_2)

    #GET RESPONSE
    data_2 = response_2.json()

    #STATUS CHECK
    assert data_2["status"] == "deleted"

    # === AGAIN DELETE PROPOSAL ===
    payload_3 = {"author_id": 1}

    #HTTP-REQUEST
    response_3 = client.request("DELETE", f"/proposals/{proposal_id}", json=payload_3)

    #GET RESPONSE
    data_3 = response_3.json()

    #STATUS CODE CHECK
    assert response_3.status_code == 404

    #RESPONSE DETAILS CHECK
    assert data_3["detail"] == "Proposal not found"

def test_start_by_non_author():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    # === START VOTING (NON AUTHOR) ===

    #PAYLOAD
    payload_2 = {"author_id": 2}

    #HTTP-REQUEST
    response_2 = client.post(f"/proposals/{proposal_id}/start", json=payload_2)

    #GET RESPONSE
    data_2 = response_2.json()

    #STATUS CODE CHECK
    assert response_2.status_code == 403

    #RESPONSE DETAILS CHECK
    assert data_2["detail"] == "Only author can perform this action"

def test_start_invalid_status():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    # === AGAIN START VOTING ===
    response_2, data_2 = _start_voting(proposal_id)

    #STATUS CODE CHECK
    assert response_2.status_code == 409

    #RESPONSE DETAILS CHECK
    assert data_2["detail"] == "Proposal in a wrong state"

# ==== VOTE TESTS ====
# ====================

def test_duplicate_vote():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #1st VOTE (GOOD)
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote1 = client.post("/votes", json=vote_payload)
    assert vote1.status_code == 200

    #2nd VOTE (BAD)
    vote2 = client.post("/votes", json=vote_payload)
    assert vote2.status_code == 409

    data = vote2.json()
    assert data["detail"] == "User already voted"

def test_not_participant():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #VOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 4,
        "value": "approve"
    }

    vote1 = client.post("/votes", json=vote_payload)
    assert vote1.status_code == 403

    data = vote1.json()
    assert data["detail"] == "User is not a participant"

def test_vote_after_finish():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    #VOTE
    vote_payload_1 = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    client.post("/votes", json=vote_payload_1)

    #FINISH VOTE
    client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 1})

    #VOTE AGAIN
    vote_payload_2 = {
        "proposal_id": proposal_id,
        "user_id": 2,
        "value": "approve"
    }

    vote2 = client.post("/votes", json=vote_payload_2)
    assert vote2.status_code == 409

    data = vote2.json()
    assert data["detail"] == "Proposal in a wrong state"

def test_revote():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    _start_voting(proposal_id)

    #VOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200

    #REVOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "reject"
    }

    vote = client.patch("/votes", json=vote_payload)
    assert vote.status_code == 200

    response = client.get(f"/proposals/{proposal_id}/votes")
    data = response.json()

    #SEARCH FOR VOTER
    votes = data["votes"]
    found_vote = None

    for vote in votes:
        if vote["user_id"] == 1:
            found_vote = vote

    #VALUE CHECK
    assert found_vote is not None
    assert found_vote["value"] == "reject"

def test_revote_without_vote_made():

    # CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    # CREATE PROPOSAL
    response, data, payload = _create_proposal()

    # FIND PROPOSAL ID
    proposal_id = data["id"]

    # START VOTING
    response, data = _start_voting(proposal_id)

    # REVOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "reject"
    }

    vote = client.patch("/votes", json=vote_payload)
    assert vote.status_code == 404

    data = vote.json()
    assert data["detail"] == "Vote not found"

def test_revote_after_finish():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    _start_voting(proposal_id)

    #VOTE_1
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200

    #VOTE_2
    vote_payload_2 = {
        "proposal_id": proposal_id,
        "user_id": 2,
        "value": "approve"
    }

    vote_2 = client.post("/votes", json=vote_payload_2)
    assert vote_2.status_code == 200

    #FINISH CHECK
    data = vote_2.json()
    assert data["status"] == "approved"

    #REVOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "reject"
    }

    vote = client.patch("/votes", json=vote_payload)
    assert vote.status_code == 409

    data = vote.json()
    assert data["detail"] == "Proposal in a wrong state"

def test_vote_after_deadline():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    # === SETUP PROPOSAL (PAYLOAD) ===
    payload = {
        "title": "Test proposal",
        "description": "Test description",
        "author_id": 1,
        "participant_ids": [1, 2],
        "deadline": str(datetime.utcnow() - timedelta(minutes=1))
    }

    #HTTP-REQUEST
    response = client.post("/proposals", json=payload)

    #GET RESPONSE
    data = response.json()

    #STATUS CODE CHECK
    assert response.status_code == 200

    #DEADLINE GOT CHECK
    assert data["deadline"] is not None

    # FIND PROPOSAL ID
    proposal_id = data["id"]

    # START VOTING
    response, data = _start_voting(proposal_id)

    # VOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 409

    data = vote.json()
    assert data["detail"] == "Proposal in a wrong state"

# ==== FINISH TESTS ====
# ======================

def test_manual_finish():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    #FINISH PROPOSAL
    response_2 = client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 1})

    data_2 = response_2.json()

    #TEST
    assert response_2.status_code == 200
    assert data_2["status"] == "rejected"

def test_finish_by_non_author():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    #FINISH PROPOSAL
    response_2 = client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 2})

    data_2 = response_2.json()

    #TEST
    assert response_2.status_code == 403
    assert data_2["detail"] == "Only author can perform this action"

def test_finish_already_finished():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    response, data = _start_voting(proposal_id)

    #STATUS CHECK
    assert data["status"] == "voting"

    #FINISH PROPOSAL
    response_2 = client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 1})

    data_2 = response_2.json()

    #PROPOSAL FINISHED CHECK
    assert response_2.status_code == 200
    assert data_2["status"] == "rejected"

    #FINISH PROPOSAL AGAIN
    response_3 = client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 1})

    data_3 = response_3.json()

    #PROPOSAL FINISHED CHECK
    assert response_3.status_code == 409
    assert data_3["detail"] == "Proposal in a wrong state"

# ==== READ TESTS ====
# ====================

def test_get_proposal_result():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    _start_voting(proposal_id)

    #VOTE_1
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200

    #VOTE_2
    vote_payload_2 = {
        "proposal_id": proposal_id,
        "user_id": 2,
        "value": "approve"
    }

    vote_2 = client.post("/votes", json=vote_payload_2)
    assert vote_2.status_code == 200

    #GET PROPOSAL RESULTS
    result = client.get(f"/proposals/{proposal_id}/result")
    assert result.status_code == 200

    result_data = result.json()

    #STATUS CHECK
    assert result_data["status"] == "approved"

def test_get_proposal_votes():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    _start_voting(proposal_id)

    #VOTE
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200

    #GET VOTES
    response = client.get(f"/proposals/{proposal_id}/votes")
    votes_data = response.json()

    #SEARCH FOR VOTER
    votes = votes_data["votes"]
    found_vote = None

    for vote in votes:
        if vote["user_id"] == 1:
            found_vote = vote

    #VALUE CHECK
    assert found_vote is not None
    assert found_vote["value"] == "approve"

# ==== AUDIT TESTS ====
# =====================

def test_audit_log():

    #CLEAR DB
    _clear_db()

    #SEED USERS
    _seed_users()

    #CREATE PROPOSAL
    response, data, payload = _create_proposal()

    #FIND PROPOSAL ID
    proposal_id = data["id"]

    #START VOTING
    _start_voting(proposal_id)

    #VOTE_1
    vote_payload = {
        "proposal_id": proposal_id,
        "user_id": 1,
        "value": "approve"
    }

    vote = client.post("/votes", json=vote_payload)
    assert vote.status_code == 200

    #FINISH PROPOSAL
    response_2 = client.post(f"/proposals/{proposal_id}/finish", json={"author_id": 1})
    assert response_2.status_code == 200

    result_data = response_2.json()
    assert result_data["status"] == "approved"

    # === AUDIT TEST (NEW SESSION) ===
    session = TestSessionLocal()

    #GET LOGS
    logs = session.query(AuditLog).filter(AuditLog.proposal_id == proposal_id).all()

    #GET ACTIONS
    actions = [log.action for log in logs]

    session.close()

    #TEST
    assert "create_proposal" in actions
    assert "start_voting" in actions
    assert "create_vote" in actions
    assert "manual_finish" in actions






