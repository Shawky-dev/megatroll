#include "megajaw_uart/MotorDriver.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <cstdio>
#include <cstring>
#include <iostream>

MotorDriver::MotorDriver(const char* port) {
    fd_ = open(port, O_RDWR | O_NOCTTY | O_SYNC);

    if (fd_ < 0) {
        std::cout << "[megajaw_uart] UART open failed on " << port << "\n";
        return;
    }

    termios tty{};
    tcgetattr(fd_, &tty);

    cfsetospeed(&tty, B115200);   // must match Serial1.begin(115200) on STM32
    cfsetispeed(&tty, B115200);

    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;           // 8-bit chars
    tty.c_cflag &= ~PARENB;       // no parity
    tty.c_cflag &= ~CSTOPB;       // 1 stop bit
    tty.c_cflag &= ~CRTSCTS;      // no hardware flow control

    tty.c_lflag = 0;  // raw — no echo, no signals
    tty.c_oflag = 0;  // raw output
    tty.c_iflag = 0;  // raw input, no CR/LF translation

    tcsetattr(fd_, TCSANOW, &tty);

    std::cout << "[megajaw_uart] UART connected on " << port << " at 115200\n";
}

MotorDriver::~MotorDriver() {
    stopMotors();
    if (fd_ >= 0)
        close(fd_);
}

void MotorDriver::stopMotors() {
    setWheelSpeeds(0.0f, 0.0f);
}

void MotorDriver::setWheelSpeeds(float left, float right) {
    if (fd_ < 0) return;

    // Clamp to [-1, 1]
    if (left  >  1.0f) left  =  1.0f;
    if (left  < -1.0f) left  = -1.0f;
    if (right >  1.0f) right =  1.0f;
    if (right < -1.0f) right = -1.0f;

    char buffer[64];
    int len = snprintf(buffer, sizeof(buffer), "M,%.2f,%.2f\n", left, right);

    ::write(fd_, buffer, len);  // :: to call POSIX write(), not ROS write()
}
