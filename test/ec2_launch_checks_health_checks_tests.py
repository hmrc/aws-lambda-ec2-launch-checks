import ec2_launch_checks_health_checks as my_mod
import unittest
import mock

# from moto import mock_ec2

# we have an lambda handler returning the result - DONE
# we have a the instance ip - mocked
# we get a 200 when hitting the goss endpoint - mocked
# handler exit 1 if we dont get  200 return form the goss endpoint


class HealthCheckTestCase(unittest.TestCase):
    event = {"detail": {"EC2InstanceId": "i-0758ddb2bc1369045"}}

    @mock.patch("ec2_launch_checks_health_checks.get_instance_ip", return_value="1.1.1.1")
    def test_lambda_handler_returns_event(self, func):
        result = my_mod.lambda_handler(self.event, "context")
        self.assertIsInstance(result, dict)

    # def test_get_instance_ip(self):
    #     expected_result = "1.1.1.1"
    #     result = my_mod.get_instance_ip("i-0758ddb2bc1369045")
    #     self.assertEquals(result, expected_result)

    # Wanted to mock this but boto does not currently cover describe instance
    # @mock_ec2
    # def test_get_intstance_ip_based_on_instance_id(self):
    #     instance_id_1 = "i-0758ddb2bc1369045"
    #     instance_id_2 = "i-0858ddb2bc7654321"

    #     expected_result_1 = "2.2.2.2"
    #     expected_result_2 = "3.3.3.3"

    #     result_1 = my_mod.get_instance_ip(instance_id_1)
    #     result_2 = my_mod.get_instance_ip(instance_id_2)

    #     self.assertEquals(result_1, expected_result_1)
    #     self.assertEquals(result_2, expected_result_2)


if __name__ == "__main__":
    unittest.main()
