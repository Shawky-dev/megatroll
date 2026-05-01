#include "megajaw_hardware/MotorDriver.hpp"
#include <iostream>
#include <pigpio.h>
#include <unistd.h>

MotorDriver::MotorDriver(int rpA, int rpB, int lpA, int lpB) {
	if (gpioInitialise() < 0)
		std::cout << "Failed to initialize PiGPIO" <<  std::endl;
	
	// Set GPIO pins as output
	gpioSetMode(lpA, PI_OUTPUT);
	gpioSetMode(lpB, PI_OUTPUT);
	gpioSetMode(rpA, PI_OUTPUT);
	gpioSetMode(rpB, PI_OUTPUT);

	this->_rpA = rpA;
	this->_rpB = rpB;
	this->_lpA = lpA;
	this->_lpB = lpB;
}

MotorDriver::~MotorDriver() {
	std::cout << "Cleaning GPIO state..." << std::endl;
	stopMotors();

	gpioTerminate();
}


void MotorDriver::stopMotors() {
	setMotors(0, _lpA, _lpB);
	setMotors(0, _rpA, _rpB);
}

void MotorDriver::setLeftMotor(float speedPerc) {
	setMotors(speedPerc, _lpA, _lpB);
}

void MotorDriver::setRightMotor(float speedPerc) {
	setMotors(speedPerc, _rpA, _rpB);
}

void MotorDriver::setMotors(float speedPerc, int pinA, int pinB) {
	if (speedPerc < -1) {
		std::cout << "Warning: speedPerc can't be below -1, got " << speedPerc << std::endl;
		speedPerc = -1;
	} else if(speedPerc > 1) {
		std::cout << "Warning: speedPerc can't be above 1, got " << speedPerc << std::endl;
		speedPerc = 1;
	}


	if (speedPerc >= 0) {
		// Forward
		gpioPWM(pinA, 0);
		gpioPWM(pinB, static_cast<int>(speedPerc * 255));
	} else {
		// Backward
		gpioPWM(pinB, 0);
		gpioPWM(pinA, static_cast<int>(std::abs(speedPerc) * 255));
	}
}
