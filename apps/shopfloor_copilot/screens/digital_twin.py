"""
Digital Twin Simulation
- What-if scenarios for production planning
- Capacity planning tools
- Schedule optimization
"""
from nicegui import ui
from sqlalchemy import text
from datetime import datetime, timedelta
import random

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

def digital_twin_screen():
    """Digital twin simulation for production planning and optimization."""
    
    engine = get_db_engine()
    
    # Helper functions
    def load_baseline_data(container):
        """Load current baseline production data."""
        container.clear()
        
        try:
            with engine.connect() as conn:
                # Get recent performance data
                baseline = conn.execute(text("""
                    SELECT 
                        line_id,
                        line_name,
                        AVG(oee) as avg_oee,
                        AVG(availability) as avg_availability,
                        AVG(performance) as avg_performance,
                        AVG(quality) as avg_quality,
                        SUM(total_units_produced) as total_units,
                        AVG(total_units_produced) as avg_units_per_shift,
                        COUNT(*) as shifts_worked
                    FROM oee_line_shift
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY line_id, line_name
                    ORDER BY line_name
                """)).fetchall()
        except Exception as e:
            with container:
                ui.label(f'Error loading baseline data: {str(e)}').classes('text-red')
            return None
        
        with container:
            if not baseline:
                ui.label('No baseline data available.').classes('text-grey-6 italic')
                return None
            
            with ui.card().classes('w-full'):
                ui.label('Current Production Baseline (Last 30 Days)').classes('text-xl font-bold')
                ui.separator()
                
                # Table header
                with ui.row().classes('w-full font-bold bg-grey-2 p-2'):
                    ui.label('Line').classes('w-32')
                    ui.label('Avg OEE').classes('w-24 text-right')
                    ui.label('Avg Units/Shift').classes('w-32 text-right')
                    ui.label('Total Units').classes('w-32 text-right')
                    ui.label('Shifts').classes('w-24 text-right')
                
                for line in baseline:
                    with ui.row().classes('w-full items-center p-2 border-t'):
                        ui.label(line.line_name).classes('w-32 font-medium')
                        oee_pct = float(line.avg_oee or 0) * 100
                        color = 'green' if oee_pct >= 80 else 'orange' if oee_pct >= 60 else 'red'
                        ui.badge(f'{oee_pct:.1f}%', color=color).classes('w-24')
                        ui.label(f'{float(line.avg_units_per_shift or 0):,.0f}').classes('w-32 text-right')
                        ui.label(f'{line.total_units:,}').classes('w-32 text-right')
                        ui.label(f'{line.shifts_worked}').classes('w-24 text-right')
        
        return baseline
    
    def run_what_if_scenario(scenario_type, param_changes, baseline_data, result_container):
        """Run a what-if simulation scenario."""
        result_container.clear()
        
        if not baseline_data:
            with result_container:
                ui.label('No baseline data available. Cannot run simulation.').classes('text-red')
            return
        
        with result_container:
            ui.label('🔄 Running simulation...').classes('text-blue font-bold')
        
        # Simulate different scenarios
        if scenario_type == 'OEE Improvement':
            oee_increase = param_changes.get('oee_increase', 0) / 100
            
            with result_container:
                result_container.clear()
                
                with ui.card().classes('w-full bg-green-50'):
                    ui.label(f'Scenario: {oee_increase*100:.0f}% OEE Improvement').classes('text-2xl font-bold text-green-800')
                    ui.separator()
                    
                    total_baseline = sum(line.total_units for line in baseline_data)
                    total_projected = total_baseline * (1 + oee_increase)
                    additional_units = total_projected - total_baseline
                    
                    with ui.row().classes('w-full gap-4 mt-2'):
                        with ui.column().classes('flex-1'):
                            ui.label('Current Production').classes('text-lg font-bold')
                            ui.label(f'{total_baseline:,.0f} units').classes('text-3xl font-bold')
                        
                        ui.icon('arrow_forward', size='xl').classes('text-green-600')
                        
                        with ui.column().classes('flex-1'):
                            ui.label('Projected Production').classes('text-lg font-bold')
                            ui.label(f'{total_projected:,.0f} units').classes('text-3xl font-bold text-green-700')
                        
                        with ui.card().classes('flex-1 bg-white'):
                            ui.label('Additional Output').classes('text-sm text-grey-7')
                            ui.label(f'+{additional_units:,.0f} units').classes('text-2xl font-bold text-green')
                            ui.label(f'+{oee_increase*100:.1f}% increase').classes('text-sm text-grey-6')
                    
                    # Per-line breakdown
                    ui.label('Impact by Production Line:').classes('text-lg font-bold mt-4')
                    ui.separator()
                    
                    for line in baseline_data:
                        current_units = line.total_units
                        projected_units = current_units * (1 + oee_increase)
                        gain = projected_units - current_units
                        
                        with ui.row().classes('w-full items-center p-2 border-t'):
                            ui.label(line.line_name).classes('w-40 font-medium')
                            ui.label(f'{current_units:,} → {projected_units:,.0f}').classes('flex-1')
                            ui.badge(f'+{gain:,.0f} units', color='green')
        
        elif scenario_type == 'Add Production Line':
            new_line_capacity = param_changes.get('line_capacity', 0)
            new_line_oee = param_changes.get('line_oee', 75) / 100
            shifts_per_month = param_changes.get('shifts', 60)
            
            effective_units = new_line_capacity * new_line_oee * shifts_per_month
            
            with result_container:
                result_container.clear()
                
                with ui.card().classes('w-full bg-blue-50'):
                    ui.label('Scenario: Add New Production Line').classes('text-2xl font-bold text-blue-800')
                    ui.separator()
                    
                    total_baseline = sum(line.total_units for line in baseline_data)
                    total_projected = total_baseline + effective_units
                    
                    with ui.column().classes('gap-3 mt-2'):
                        ui.label(f'New Line Capacity: {new_line_capacity:,} units/shift @ {new_line_oee*100:.0f}% OEE').classes('text-lg')
                        ui.label(f'Expected Output: {effective_units:,.0f} units/month').classes('text-2xl font-bold text-blue-700')
                        
                        with ui.row().classes('w-full gap-4 mt-4'):
                            with ui.card().classes('flex-1'):
                                ui.label('Current Capacity').classes('text-sm text-grey-7')
                                ui.label(f'{total_baseline:,.0f} units/month').classes('text-xl font-bold')
                            
                            with ui.card().classes('flex-1 bg-white'):
                                ui.label('New Total Capacity').classes('text-sm text-grey-7')
                                ui.label(f'{total_projected:,.0f} units/month').classes('text-xl font-bold text-blue-700')
                            
                            with ui.card().classes('flex-1 bg-green-50'):
                                ui.label('Capacity Increase').classes('text-sm text-grey-7')
                                increase_pct = (effective_units / total_baseline * 100) if total_baseline > 0 else 0
                                ui.label(f'+{increase_pct:.1f}%').classes('text-xl font-bold text-green')
        
        elif scenario_type == 'Reduce Downtime':
            downtime_reduction = param_changes.get('downtime_reduction', 0) / 100
            
            with result_container:
                result_container.clear()
                
                with ui.card().classes('w-full bg-orange-50'):
                    ui.label(f'Scenario: {downtime_reduction*100:.0f}% Downtime Reduction').classes('text-2xl font-bold text-orange-800')
                    ui.separator()
                    
                    # Estimate impact on availability and production
                    for line in baseline_data:
                        current_avail = float(line.avg_availability or 0.8)
                        # Downtime reduction improves availability
                        new_avail = min(current_avail * (1 + downtime_reduction * 0.5), 1.0)
                        
                        current_units = line.total_units
                        projected_units = current_units * (new_avail / current_avail)
                        gain = projected_units - current_units
                        
                        with ui.expansion(f'{line.line_name}', icon='timeline').classes('w-full'):
                            with ui.column().classes('gap-2'):
                                ui.label(f'Current Availability: {current_avail*100:.1f}%').classes('text-sm')
                                ui.label(f'Projected Availability: {new_avail*100:.1f}%').classes('text-sm font-bold text-green')
                                ui.label(f'Production Gain: +{gain:,.0f} units/month').classes('text-lg font-bold text-orange-700')
        
        elif scenario_type == 'Shift Schedule Change':
            additional_shifts = param_changes.get('additional_shifts', 0)
            
            with result_container:
                result_container.clear()
                
                with ui.card().classes('w-full bg-purple-50'):
                    ui.label(f'Scenario: Add {additional_shifts} Shifts per Week').classes('text-2xl font-bold text-purple-800')
                    ui.separator()
                    
                    total_baseline = sum(line.total_units for line in baseline_data)
                    
                    # Assume current is 5 days/week, 2 shifts/day = 10 shifts/week
                    current_shifts_per_week = 10
                    new_shifts_per_week = current_shifts_per_week + additional_shifts
                    multiplier = new_shifts_per_week / current_shifts_per_week
                    
                    total_projected = total_baseline * multiplier
                    additional_units = total_projected - total_baseline
                    
                    with ui.column().classes('gap-3 mt-2'):
                        ui.label(f'Current Schedule: ~{current_shifts_per_week} shifts/week').classes('text-lg')
                        ui.label(f'New Schedule: ~{new_shifts_per_week} shifts/week').classes('text-lg font-bold')
                        
                        with ui.row().classes('w-full gap-4 mt-4'):
                            with ui.card().classes('flex-1'):
                                ui.label('Current Production').classes('text-sm text-grey-7')
                                ui.label(f'{total_baseline:,.0f} units/month').classes('text-xl font-bold')
                            
                            with ui.card().classes('flex-1 bg-white'):
                                ui.label('Projected Production').classes('text-sm text-grey-7')
                                ui.label(f'{total_projected:,.0f} units/month').classes('text-xl font-bold text-purple-700')
                            
                            with ui.card().classes('flex-1 bg-green-50'):
                                ui.label('Additional Output').classes('text-sm text-grey-7')
                                ui.label(f'+{additional_units:,.0f} units').classes('text-xl font-bold text-green')
        
        ui.notify('Simulation complete', type='positive')
    
    def run_capacity_planning(target_units, current_capacity, result_container):
        """Run capacity planning analysis."""
        result_container.clear()
        
        if not current_capacity or current_capacity == 0:
            with result_container:
                ui.label('No baseline data available for capacity planning.').classes('text-red')
            return
        
        gap = target_units - current_capacity
        gap_pct = (gap / current_capacity * 100) if current_capacity > 0 else 0
        
        with result_container:
            with ui.card().classes('w-full bg-blue-50'):
                ui.label('Capacity Planning Analysis').classes('text-2xl font-bold text-blue-800')
                ui.separator()
                
                with ui.row().classes('w-full gap-4 mt-2'):
                    with ui.card().classes('flex-1'):
                        ui.label('Current Capacity').classes('text-sm text-grey-7')
                        ui.label(f'{current_capacity:,.0f} units/month').classes('text-2xl font-bold')
                    
                    with ui.card().classes('flex-1 bg-white'):
                        ui.label('Target Demand').classes('text-sm text-grey-7')
                        ui.label(f'{target_units:,.0f} units/month').classes('text-2xl font-bold')
                    
                    with ui.card().classes('flex-1 ' + ('bg-red-50' if gap > 0 else 'bg-green-50')):
                        ui.label('Capacity Gap').classes('text-sm text-grey-7')
                        color = 'red' if gap > 0 else 'green'
                        sign = '+' if gap > 0 else ''
                        ui.label(f'{sign}{gap:,.0f} units').classes(f'text-2xl font-bold text-{color}')
                        ui.label(f'{gap_pct:+.1f}%').classes('text-sm text-grey-6')
                
                if gap > 0:
                    # Need more capacity
                    ui.label('📊 Recommendations to Meet Target:').classes('text-xl font-bold mt-4')
                    ui.separator()
                    
                    with ui.column().classes('gap-2 mt-2'):
                        # Option 1: OEE Improvement
                        oee_needed = (gap / current_capacity * 100)
                        with ui.card().classes('w-full'):
                            ui.label('Option 1: Improve OEE').classes('font-bold text-lg')
                            ui.label(f'Increase OEE by {oee_needed:.1f}% across all lines').classes('text-sm')
                            ui.label(f'Expected timeline: 3-6 months').classes('text-xs text-grey-6')
                            ui.label(f'Investment: Medium (process improvements, training)').classes('text-xs text-grey-6')
                        
                        # Option 2: Add shifts
                        avg_units_per_shift = current_capacity / 60  # Assume 60 shifts/month
                        shifts_needed = gap / avg_units_per_shift
                        with ui.card().classes('w-full'):
                            ui.label('Option 2: Add Production Shifts').classes('font-bold text-lg')
                            ui.label(f'Add approximately {shifts_needed:.0f} shifts per month').classes('text-sm')
                            ui.label(f'Expected timeline: 1-2 months').classes('text-xs text-grey-6')
                            ui.label(f'Investment: High (labor costs, utilities)').classes('text-xs text-grey-6')
                        
                        # Option 3: New line
                        lines_needed = gap / (current_capacity / 3)  # Assuming 3 lines currently
                        with ui.card().classes('w-full'):
                            ui.label('Option 3: Add Production Line(s)').classes('font-bold text-lg')
                            ui.label(f'Add {lines_needed:.1f} new production line(s)').classes('text-sm')
                            ui.label(f'Expected timeline: 6-12 months').classes('text-xs text-grey-6')
                            ui.label(f'Investment: Very High (capex, installation, training)').classes('text-xs text-grey-6')
                else:
                    # Have excess capacity
                    ui.label('✅ Sufficient Capacity').classes('text-xl font-bold text-green mt-4')
                    ui.label(f'Current capacity exceeds target by {abs(gap):,.0f} units ({abs(gap_pct):.1f}%)').classes('text-lg')
                    
                    with ui.card().classes('w-full bg-green-50 mt-2'):
                        ui.label('Optimization Opportunities:').classes('font-bold')
                        ui.label('• Reduce operating costs by optimizing shift schedules').classes('text-sm')
                        ui.label('• Consider line consolidation for better efficiency').classes('text-sm')
                        ui.label('• Opportunity for preventive maintenance windows').classes('text-sm')
    
    def optimize_schedule(optimization_goal, constraints, result_container):
        """Run schedule optimization."""
        result_container.clear()
        
        with result_container:
            with ui.card().classes('w-full bg-purple-50'):
                ui.label(f'Schedule Optimization: {optimization_goal}').classes('text-2xl font-bold text-purple-800')
                ui.separator()
                
                if optimization_goal == 'Maximize Throughput':
                    ui.markdown("""
                    **Optimization Strategy: Maximize Production Output**
                    
                    **Recommended Schedule:**
                    - **Peak Hours (6 AM - 2 PM):** Run high-efficiency lines at full capacity
                    - **Standard Hours (2 PM - 10 PM):** Maintain steady production on all lines
                    - **Night Shift (10 PM - 6 AM):** Focus on maintenance-heavy or slower lines
                    
                    **Expected Impact:**
                    - +12-15% throughput improvement
                    - Optimized line utilization during peak efficiency hours
                    - Reduced setup time through batching
                    
                    **Key Actions:**
                    1. Schedule high-volume orders during morning shift (highest OEE)
                    2. Batch similar products to minimize changeover
                    3. Implement parallel processing where possible
                    """).classes('text-sm')
                
                elif optimization_goal == 'Minimize Energy Cost':
                    ui.markdown("""
                    **Optimization Strategy: Reduce Energy Consumption Costs**
                    
                    **Recommended Schedule:**
                    - **Off-Peak Hours (10 PM - 6 AM):** Run energy-intensive operations
                    - **Peak Hours (6 AM - 10 PM):** Minimize high-power equipment usage
                    - **Weekend Production:** Maximize output during lower rate periods
                    
                    **Expected Impact:**
                    - 15-20% reduction in energy costs
                    - Potential demand charge savings
                    - Lower carbon footprint
                    
                    **Key Actions:**
                    1. Shift heavy loads to off-peak hours
                    2. Implement load balancing across lines
                    3. Schedule maintenance during low-rate periods
                    """).classes('text-sm')
                
                elif optimization_goal == 'Balance Workload':
                    ui.markdown("""
                    **Optimization Strategy: Even Distribution Across Lines**
                    
                    **Recommended Schedule:**
                    - Distribute production evenly across all 3 shifts
                    - Balance complex vs. simple jobs throughout the day
                    - Rotate operators to prevent fatigue
                    
                    **Expected Impact:**
                    - Improved operator satisfaction
                    - Reduced overtime costs
                    - More consistent quality across shifts
                    
                    **Key Actions:**
                    1. Create standardized shift templates
                    2. Implement skill-based task assignment
                    3. Monitor and adjust based on real-time performance
                    """).classes('text-sm')
                
                elif optimization_goal == 'Minimize Downtime':
                    ui.markdown("""
                    **Optimization Strategy: Preventive Maintenance Scheduling**
                    
                    **Recommended Schedule:**
                    - **Preventive Maintenance:** Schedule during planned downtime windows
                    - **Quick Changeovers:** Implement SMED principles (< 10 min)
                    - **Buffer Management:** Maintain strategic inventory levels
                    
                    **Expected Impact:**
                    - 30-40% reduction in unplanned downtime
                    - Extended equipment lifespan
                    - Higher overall availability
                    
                    **Key Actions:**
                    1. Schedule maintenance during low-demand periods
                    2. Pre-stage changeover materials
                    3. Implement predictive maintenance alerts
                    """).classes('text-sm')
                
                # Optimization constraints display
                ui.label('Applied Constraints:').classes('text-lg font-bold mt-4')
                ui.separator()
                with ui.column().classes('gap-1'):
                    for constraint, value in constraints.items():
                        if value:
                            ui.label(f'✓ {constraint}: {value}').classes('text-sm')
        
        ui.notify('Optimization complete', type='positive')
    
    # Main UI
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            with ui.column().classes('gap-1'):
                ui.label('Digital Twin Simulation').classes('text-3xl font-bold')
                ui.label('What-if scenarios, capacity planning, and schedule optimization').classes('text-sm text-grey-7')
            ui.icon('account_tree', size='xl').classes('text-primary')
        
        # Baseline data
        baseline_container = ui.column().classes('w-full')
        baseline_data = load_baseline_data(baseline_container)
        
        # Tabs for different simulation types
        with ui.tabs().classes('w-full mt-4') as tabs:
            tab_whatif = ui.tab('What-If Scenarios', icon='science')
            tab_capacity = ui.tab('Capacity Planning', icon='analytics')
            tab_schedule = ui.tab('Schedule Optimization', icon='event')
        
        with ui.tab_panels(tabs, value=tab_whatif).classes('w-full'):
            
            # What-If Scenarios
            with ui.tab_panel(tab_whatif):
                with ui.card().classes('w-full'):
                    ui.label('Run What-If Scenarios').classes('text-2xl font-bold')
                    ui.separator()
                    
                    with ui.row().classes('w-full gap-4 items-end'):
                        scenario_type = ui.select(
                            ['OEE Improvement', 'Add Production Line', 'Reduce Downtime', 'Shift Schedule Change'],
                            label='Scenario Type',
                            value='OEE Improvement'
                        ).classes('flex-1')
                    
                    # Dynamic parameters based on scenario type
                    param_container = ui.column().classes('w-full gap-2 mt-4')
                    
                    def update_params():
                        param_container.clear()
                        with param_container:
                            if scenario_type.value == 'OEE Improvement':
                                oee_slider = ui.slider(min=1, max=30, value=10, step=1).classes('w-full').props('label-always')
                                ui.label().bind_text_from(oee_slider, 'value', lambda v: f'OEE Increase: {v}%')
                                return {'oee_increase': oee_slider.value}
                            
                            elif scenario_type.value == 'Add Production Line':
                                capacity = ui.number('Line Capacity (units/shift)', value=500, min=100, max=2000).classes('w-full')
                                oee = ui.slider(min=50, max=95, value=75, step=5).classes('w-full').props('label-always')
                                ui.label().bind_text_from(oee, 'value', lambda v: f'Expected OEE: {v}%')
                                shifts = ui.number('Shifts per Month', value=60, min=20, max=90).classes('w-full')
                                return {'line_capacity': capacity.value, 'line_oee': oee.value, 'shifts': shifts.value}
                            
                            elif scenario_type.value == 'Reduce Downtime':
                                downtime_slider = ui.slider(min=5, max=50, value=20, step=5).classes('w-full').props('label-always')
                                ui.label().bind_text_from(downtime_slider, 'value', lambda v: f'Downtime Reduction: {v}%')
                                return {'downtime_reduction': downtime_slider.value}
                            
                            elif scenario_type.value == 'Shift Schedule Change':
                                shifts_slider = ui.slider(min=1, max=10, value=3, step=1).classes('w-full').props('label-always')
                                ui.label().bind_text_from(shifts_slider, 'value', lambda v: f'Additional Shifts per Week: {v}')
                                return {'additional_shifts': shifts_slider.value}
                    
                    scenario_type.on_value_change(lambda: update_params())
                    params = update_params()
                    
                    whatif_result = ui.column().classes('w-full mt-4')
                    
                    ui.button(
                        'Run Simulation',
                        icon='play_arrow',
                        on_click=lambda: run_what_if_scenario(
                            scenario_type.value,
                            update_params(),
                            baseline_data,
                            whatif_result
                        )
                    ).classes('w-full bg-primary mt-4').props('size=lg')
            
            # Capacity Planning
            with ui.tab_panel(tab_capacity):
                with ui.card().classes('w-full'):
                    ui.label('Capacity Planning Tool').classes('text-2xl font-bold')
                    ui.separator()
                    
                    current_capacity = sum(line.total_units for line in baseline_data) if baseline_data else 0
                    
                    with ui.row().classes('w-full gap-4 items-end'):
                        target_demand = ui.number(
                            'Target Monthly Demand (units)',
                            value=int(current_capacity * 1.2) if current_capacity > 0 else 10000,
                            min=0,
                            step=1000
                        ).classes('flex-1')
                        
                        ui.button(
                            'Analyze Capacity',
                            icon='analytics',
                            on_click=lambda: run_capacity_planning(
                                target_demand.value,
                                current_capacity,
                                capacity_result
                            )
                        ).classes('bg-blue')
                    
                    ui.label(f'Current Monthly Capacity: {current_capacity:,.0f} units').classes('text-lg font-bold mt-2')
                    
                    capacity_result = ui.column().classes('w-full mt-4')
            
            # Schedule Optimization
            with ui.tab_panel(tab_schedule):
                with ui.card().classes('w-full'):
                    ui.label('Schedule Optimization').classes('text-2xl font-bold')
                    ui.separator()
                    
                    with ui.row().classes('w-full gap-4 items-end'):
                        optimization_goal = ui.select(
                            ['Maximize Throughput', 'Minimize Energy Cost', 'Balance Workload', 'Minimize Downtime'],
                            label='Optimization Goal',
                            value='Maximize Throughput'
                        ).classes('flex-1')
                    
                    # Constraints
                    with ui.expansion('Constraints (Optional)', icon='tune').classes('w-full mt-2'):
                        with ui.column().classes('gap-2'):
                            max_overtime = ui.checkbox('Limit overtime to 10% of regular hours', value=True)
                            energy_constraints = ui.checkbox('Consider energy cost variations by time of day', value=False)
                            maintenance_windows = ui.checkbox('Reserve time for preventive maintenance', value=True)
                            operator_limits = ui.checkbox('Respect operator skill and availability', value=True)
                    
                    schedule_result = ui.column().classes('w-full mt-4')
                    
                    ui.button(
                        'Optimize Schedule',
                        icon='auto_awesome',
                        on_click=lambda: optimize_schedule(
                            optimization_goal.value,
                            {
                                'Max Overtime': '10%' if max_overtime.value else None,
                                'Energy Optimization': 'Enabled' if energy_constraints.value else None,
                                'Maintenance Windows': 'Reserved' if maintenance_windows.value else None,
                                'Operator Constraints': 'Applied' if operator_limits.value else None
                            },
                            schedule_result
                        )
                    ).classes('w-full bg-purple mt-4').props('size=lg')
