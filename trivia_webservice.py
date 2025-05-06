from flask import Flask, request, jsonify
import requests
import uuid
import threading
import queue
import time


app = Flask(__name__)

# Thread-safe structures
request_queue = queue.Queue()
results_store = {}

# Background worker function
def worker():
    while True:
        req_id, category, n_questions = request_queue.get()
        try:
            url = f"https://opentdb.com/api.php?amount={n_questions}&category={category}"
            response = requests.get(url)
            results_store[req_id] = response.json()
            time.sleep(5)
        except Exception as e:
            results_store[req_id] = {"error": str(e)}
        request_queue.task_done()

# Start background worker thread
threading.Thread(target=worker, daemon=True).start()

@app.route("/status/<request_id>", methods=["GET"])
def check_status(request_id):
    """
    Check if a trivia request has finished processing.
    Returns:
        {"status": "finished"} if done,
        {"status": "processing"} if still in queue/processing.
    """
    if request_id in results_store:
        return jsonify({"status": "finished"}), 200
    else:
        return jsonify({"status": "processing"}), 202


@app.route("/question/", methods=['GET'])
def request_trivia():
    try:
        category = request.args.get('category', default="", type=int)
        n_questions = request.args.get('num_questions', default = 1, type=int)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    req_id = str(uuid.uuid4())
    request_queue.put((req_id, category, n_questions))
    return jsonify({"request_id": req_id}), 202  # Accepted, processing started


@app.route("/result/<request_id>", methods=["GET"])
def get_result(request_id):
    result = results_store.get(request_id)
    if result is None:
        return jsonify({"status": "processing"}), 202
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)