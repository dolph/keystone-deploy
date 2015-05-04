import locust


class WebsiteTasks(locust.TaskSet):
    def on_start(self):
        pass

    @locust.task(1)
    def multiple_choice_response(self):
        self.client.get('/')


class WebsiteUser(locust.HttpLocust):
    task_set = WebsiteTasks
    min_wait = 0
    max_wait = 1000  # auth=100, validate=100, create_user=1000
