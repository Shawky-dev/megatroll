#include "megajaw_uart/MotorDriver.hpp"
#include "hardware_interface/system_interface.hpp"
#include "rclcpp/rclcpp.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace megajaw_uart {

class MegaJawUartHardware : public hardware_interface::SystemInterface {
public:

    CallbackReturn on_init(
        const hardware_interface::HardwareComponentInterfaceParams & params) override
    {
        if (hardware_interface::SystemInterface::on_init(params) != CallbackReturn::SUCCESS)
            return CallbackReturn::ERROR;

        // Find left and right joint indices by name
        for (size_t i = 0; i < info_.joints.size(); i++) {
            if (info_.joints[i].name == "left_wheel_base_joint")  left_idx_  = i;
            else if (info_.joints[i].name == "right_wheel_base_joint") right_idx_ = i;
        }

        // Read UART port from xacro param — defaults to /dev/ttyAMA0
        std::string port = "/dev/ttyAMA0";
        if (info_.hardware_parameters.count("uart_port"))
            port = info_.hardware_parameters.at("uart_port");

        driver_ = std::make_unique<MotorDriver>(port.c_str());

        hw_commands_.resize(info_.joints.size(), 0.0);
        hw_states_pos_.resize(info_.joints.size(), 0.0);
        hw_states_vel_.resize(info_.joints.size(), 0.0);

        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> export_state_interfaces() override {
        std::vector<hardware_interface::StateInterface> state_interfaces;
        for (size_t i = 0; i < info_.joints.size(); i++) {
            state_interfaces.emplace_back(info_.joints[i].name, "position", &hw_states_pos_[i]);
            state_interfaces.emplace_back(info_.joints[i].name, "velocity", &hw_states_vel_[i]);
        }
        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override {
        std::vector<hardware_interface::CommandInterface> command_interfaces;
        for (size_t i = 0; i < info_.joints.size(); i++) {
            command_interfaces.emplace_back(info_.joints[i].name, "velocity", &hw_commands_[i]);
        }
        return command_interfaces;
    }

    hardware_interface::return_type read(
        const rclcpp::Time &, const rclcpp::Duration & period) override
    {
        for (size_t i = 0; i < hw_states_pos_.size(); i++) {
            hw_states_vel_[i] = hw_commands_[i];
            hw_states_pos_[i] += hw_states_vel_[i] * period.seconds();
        }
        return hardware_interface::return_type::OK;
    }

    hardware_interface::return_type write(
        const rclcpp::Time &, const rclcpp::Duration &) override
    {
        // hw_commands_ come in as rad/s from diff_drive_controller
        // divide by 100 matches the scaling your original plugin used
        float left_pct  = static_cast<float>(hw_commands_[left_idx_])  / 100.0f;
        float right_pct = static_cast<float>(hw_commands_[right_idx_]) / 100.0f;

        driver_->setWheelSpeeds(left_pct, right_pct);

        return hardware_interface::return_type::OK;
    }

private:
    std::unique_ptr<MotorDriver> driver_;
    size_t left_idx_ = 0, right_idx_ = 1;
    std::vector<double> hw_commands_, hw_states_pos_, hw_states_vel_;
};

}  // namespace megajaw_uart

PLUGINLIB_EXPORT_CLASS(megajaw_uart::MegaJawUartHardware, hardware_interface::SystemInterface)
