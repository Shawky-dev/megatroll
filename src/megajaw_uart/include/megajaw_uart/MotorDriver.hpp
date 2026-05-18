#ifndef MEGAJAW_UART_MOTOR_DRIVER_HPP
#define MEGAJAW_UART_MOTOR_DRIVER_HPP

class MotorDriver {
public:
    explicit MotorDriver(const char* port);
    ~MotorDriver();

    void setWheelSpeeds(float left, float right);
    void stopMotors();

private:
    int fd_;
};

#endif
