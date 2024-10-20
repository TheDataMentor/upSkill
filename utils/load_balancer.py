import redis
import json
import time
import threading
from app import redis_client

class LoadBalancer:
    def __init__(self, queue_name='task_queue'):
        self.queue_name = queue_name
        self.redis_client = redis_client

    def enqueue_task(self, task):
        self.redis_client.rpush(self.queue_name, json.dumps(task))

    def dequeue_task(self):
        task = self.redis_client.blpop(self.queue_name, timeout=1)
        if task:
            return json.loads(task[1])
        return None

    def process_tasks(self, worker_function):
        while True:
            task = self.dequeue_task()
            if task:
                worker_function(task)
            else:
                time.sleep(0.1)  # Sleep briefly to avoid busy-waiting

def start_worker(worker_function):
    load_balancer = LoadBalancer()
    worker_thread = threading.Thread(target=load_balancer.process_tasks, args=(worker_function,))
    worker_thread.start()
    return worker_thread

# Example usage:
# def example_worker(task):
#     print(f"Processing task: {task}")
#
# start_worker(example_worker)
