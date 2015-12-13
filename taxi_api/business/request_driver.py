__author__ = 'luiz'

from base import BaseBus
from taxi_api.helpers.exceptions import UserHasActiveRequest
from taxi_api.helpers.helpers import Helpers


class RequestDriverBus(BaseBus):
    _ref = "request_driver"

    def list_active_per_user(self, requester_id):
        return self.search_by_field_value(
            ["requester_id", "status"], [requester_id, "active"])

    def cancel_active_requests(self, requester_id):
        for request in self.list_active_per_user(requester_id):
            request.status = "canceled"
            self.save(request)

    def create_request(self, to_obj, **args):
        if isinstance(to_obj, dict):
            to_obj = self.to_class(**to_obj)

        # check if user already has an active request
        active_requests = list(self.list_active_per_user(to_obj.requester_id))

        if len(active_requests) > 0:
            raise UserHasActiveRequest()

        result = self.create(to_obj, **args)
        try:
            # send message to external service to find and notify drivers
            # to meet the request
            Helpers.dispatch(
                "find_and_notify_drivers",
                "New driver request: %s" % result.serialize()
            )
            return result
        except Exception as e:
            self.cancel_active_requests(to_obj.requester_id)
            raise e