#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class ActuatorNode : public rclcpp::Node {
public:
    ActuatorNode() : Node("actuator_node") {
        subscription_ = this->create_subscription<std_msgs::msg::String>(
            "heartbeat", 10, std::bind(&ActuatorNode::topic_callback, this, std::placeholders::_1));
        RCLCPP_INFO(this->get_logger(), "C++ Actuator Node is waiting for Heartbeat...");
    }

private:
    void topic_callback(const std_msgs::msg::String::SharedPtr msg) const {
        RCLCPP_INFO(this->get_logger(), "Actuator received: '%s'", msg->data.c_str());
    }
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ActuatorNode>());
    rclcpp::shutdown();
    return 0;
}
