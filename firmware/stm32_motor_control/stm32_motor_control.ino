#include <Arduino.h>

constexpr uint8_t L_A = A0;
constexpr uint8_t L_B = A1;
constexpr uint8_t R_A = A2;
constexpr uint8_t R_B = A3;

static void setMotor(uint8_t pinA, uint8_t pinB, int pwm)
{
    pwm = constrain(pwm, -255, 255);

    if (pwm > 0)
    {
        analogWrite(pinA, pwm);
        analogWrite(pinB, 0);
    }
    else if (pwm < 0)
    {
        analogWrite(pinA, 0);
        analogWrite(pinB, -pwm);
    }
    else
    {
        analogWrite(pinA, 0);
        analogWrite(pinB, 0);
    }
}

static bool parsePacket(const String &line, int &left, int &right)
{
    return sscanf(line.c_str(), "M,%d,%d", &left, &right) == 2;
}

void setup()
{
    pinMode(L_A, OUTPUT);
    pinMode(L_B, OUTPUT);
    pinMode(R_A, OUTPUT);
    pinMode(R_B, OUTPUT);

    setMotor(L_A, L_B, 0);
    setMotor(R_A, R_B, 0);

    Serial1.begin(115200);
    Serial1.setTimeout(20);
}

void loop()
{
    static unsigned long last_cmd_ms = 0;

    if (Serial1.available())
    {
        String line = Serial1.readStringUntil('\n');
        line.trim();

        int left = 0, right = 0;
        if (parsePacket(line, left, right))
        {
            setMotor(L_A, L_B, left);
            setMotor(R_A, R_B, right);
            last_cmd_ms = millis();
        }
    }

    // fail-safe stop
    if (millis() - last_cmd_ms > 200)
    {
        setMotor(L_A, L_B, 0);
        setMotor(R_A, R_B, 0);
    }
}
