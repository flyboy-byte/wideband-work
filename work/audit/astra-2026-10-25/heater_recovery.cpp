// Independent sequence tests; uses the existing fixture and actual production controller/PID.
#include "../../../test/tests/test_heater_update.cpp"
#include <cstdio>
#include <cmath>

TEST_F(HeaterUpdate, AuditRecoveryAfterLongHotClamp)
{
    ReachClosedLoop();
    sampler.esr = 200; sampler.temperature = 840;
    Run(60);
    ASSERT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    EXPECT_EQ(dut->lastDuty, 0);
    sampler.esr = 300; sampler.temperature = 780;
    Run(.05f);
    float first = dut->lastDuty;
    Run(1);
    std::printf("RECOVERY first=%.6f settled=%.6f effective=%.3f V\n", first, dut->lastDuty, 13*std::sqrt(dut->lastDuty));
    EXPECT_GT(dut->lastDuty, 0);
    EXPECT_NEAR(dut->lastDuty, Duty(4.5f,13), 1e-5);
    sampler.esr = 320; sampler.temperature = 771;
    Run(1);
    std::printf("COOLER duty=%.6f effective=%.3f V\n", dut->lastDuty, 13*std::sqrt(dut->lastDuty));
    EXPECT_GT(dut->lastDuty, Duty(7.5f,13));
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
}

TEST_F(HeaterUpdate, AuditRepeatedClampAndRecovery)
{
    ReachClosedLoop();
    for(int i=0;i<30;i++) {
        sampler.esr=200; sampler.temperature=840; Run(1);
        ASSERT_EQ(dut->lastDuty,0);
        sampler.esr=320; sampler.temperature=771; Run(1);
        EXPECT_GT(dut->lastDuty,0);
        EXPECT_LE(dut->lastDuty,Duty(12,13));
        EXPECT_EQ(dut->GetHeaterState(),HeaterState::ClosedLoop);
    }
}
