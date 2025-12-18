"""
Demo OPC UA Server for OPC Explorer Testing
Simulates a manufacturing line with various node types
"""
import asyncio
import random
from asyncua import Server, ua
from datetime import datetime


async def main():
    server = Server()
    await server.init()
    
    server.set_endpoint("opc.tcp://0.0.0.0:4850/demo/server")
    server.set_server_name("Demo OPC UA Server")
    
    # Setup security (allow anonymous)
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    
    # Register namespace
    uri = "http://demo.opcua.server/manufacturing"
    idx = await server.register_namespace(uri)
    
    # Get Objects node
    objects = server.nodes.objects
    
    # Create manufacturing structure
    factory = await objects.add_object(idx, "Factory")
    
    # Production Line 1
    line1 = await factory.add_object(idx, "ProductionLine1")
    
    # Station 1 - Assembly
    station1 = await line1.add_object(idx, "Station1_Assembly")
    temp1 = await station1.add_variable(idx, "Temperature", 25.0)
    await temp1.set_writable()
    speed1 = await station1.add_variable(idx, "Speed", 100.0)
    await speed1.set_writable()
    status1 = await station1.add_variable(idx, "Status", "Running")
    await status1.set_writable()
    counter1 = await station1.add_variable(idx, "ProductCount", 0)
    await counter1.set_writable()
    
    # Station 2 - Welding
    station2 = await line1.add_object(idx, "Station2_Welding")
    temp2 = await station2.add_variable(idx, "Temperature", 450.0)
    await temp2.set_writable()
    current2 = await station2.add_variable(idx, "WeldCurrent", 180.0)
    await current2.set_writable()
    status2 = await station2.add_variable(idx, "Status", "Running")
    await status2.set_writable()
    quality2 = await station2.add_variable(idx, "QualityScore", 95.0)
    await quality2.set_writable()
    
    # Station 3 - Testing
    station3 = await line1.add_object(idx, "Station3_Testing")
    pressure3 = await station3.add_variable(idx, "Pressure", 6.5)
    await pressure3.set_writable()
    status3 = await station3.add_variable(idx, "Status", "Running")
    await status3.set_writable()
    pass_rate3 = await station3.add_variable(idx, "PassRate", 98.5)
    await pass_rate3.set_writable()
    
    # Production Line 2
    line2 = await factory.add_object(idx, "ProductionLine2")
    
    # Robot Station
    robot = await line2.add_object(idx, "RobotStation")
    pos_x = await robot.add_variable(idx, "PositionX", 0.0)
    await pos_x.set_writable()
    pos_y = await robot.add_variable(idx, "PositionY", 0.0)
    await pos_y.set_writable()
    pos_z = await robot.add_variable(idx, "PositionZ", 0.0)
    await pos_z.set_writable()
    robot_status = await robot.add_variable(idx, "Status", "Idle")
    await robot_status.set_writable()
    
    # Quality Control
    qc = await line2.add_object(idx, "QualityControl")
    defect_rate = await qc.add_variable(idx, "DefectRate", 1.2)
    await defect_rate.set_writable()
    inspected = await qc.add_variable(idx, "InspectedCount", 0)
    await inspected.set_writable()
    
    # System monitoring
    system = await factory.add_object(idx, "SystemMonitoring")
    timestamp = await system.add_variable(idx, "Timestamp", datetime.now().isoformat())
    await timestamp.set_writable()
    alarm_count = await system.add_variable(idx, "ActiveAlarms", 0)
    await alarm_count.set_writable()
    production_rate = await system.add_variable(idx, "ProductionRate", 120.0)
    await production_rate.set_writable()
    
    print("Demo OPC UA Server starting...")
    print("Endpoint: opc.tcp://0.0.0.0:4850/demo/server")
    print("Namespace: " + uri)
    
    async with server:
        print("Server is running!")
        
        count = 0
        inspected_count = 0
        
        while True:
            await asyncio.sleep(2)
            
            # Simulate changing values
            count += 1
            inspected_count += random.randint(5, 15)
            
            # Update temperatures with noise
            await temp1.write_value(25.0 + random.uniform(-2, 3))
            await temp2.write_value(450.0 + random.uniform(-10, 15))
            
            # Update speeds and currents
            await speed1.write_value(100.0 + random.uniform(-5, 5))
            await current2.write_value(180.0 + random.uniform(-5, 5))
            
            # Update pressure
            await pressure3.write_value(6.5 + random.uniform(-0.5, 0.5))
            
            # Update counters
            await counter1.write_value(count)
            await inspected.write_value(inspected_count)
            
            # Update quality metrics
            await quality2.write_value(95.0 + random.uniform(-3, 2))
            await pass_rate3.write_value(98.5 + random.uniform(-1, 1))
            await defect_rate.write_value(max(0, 1.2 + random.uniform(-0.5, 0.5)))
            
            # Update robot position
            await pos_x.write_value(random.uniform(-100, 100))
            await pos_y.write_value(random.uniform(-100, 100))
            await pos_z.write_value(random.uniform(0, 50))
            
            # Update system monitoring
            await timestamp.write_value(datetime.now().isoformat())
            await production_rate.write_value(120.0 + random.uniform(-10, 10))
            
            # Randomly trigger alarms
            if random.random() < 0.1:
                await alarm_count.write_value(random.randint(0, 3))
            
            # Occasionally change statuses
            if count % 10 == 0:
                statuses = ["Running", "Running", "Running", "Idle", "Maintenance"]
                await status1.write_value(random.choice(statuses))
                await status2.write_value(random.choice(statuses))
                await status3.write_value(random.choice(statuses))
                await robot_status.write_value(random.choice(["Idle", "Running", "Moving"]))


if __name__ == "__main__":
    asyncio.run(main())
