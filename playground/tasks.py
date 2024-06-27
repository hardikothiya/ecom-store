import time
# from storefront.celery import celery
from celery import shared_task

# @celery.task()
@shared_task()
def notify_customer(message):
    print('Sending 10000 emails...')
    print(message)
    time.sleep(10)
    print("Task completed")