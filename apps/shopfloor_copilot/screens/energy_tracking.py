"""
Energy Consumption Tracking
- Power usage per line/station
- Correlation with production rates
- Sustainability metrics
"""
from nicegui import ui
from sqlalchemy import text
from datetime import datetime, timedelta
import math

from apps.shopfloor_copilot.routers.oee_analytics import get_db_engine

def energy_tracking_screen():
    """Energy consumption tracking and sustainability metrics."""
    
    engine = get_db_engine()
    
    # Helper functions
    def load_energy_overview(container, days):
        """Load energy consumption overview."""
        container.clear()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            with engine.connect() as conn:
                # Ensure energy tracking table exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS energy_consumption (
                        id SERIAL PRIMARY KEY,
                        line_id VARCHAR(50),
                        station_id VARCHAR(50),
                        date DATE,
                        shift VARCHAR(10),
                        energy_kwh DECIMAL(10,2),
                        peak_power_kw DECIMAL(10,2),
                        units_produced INTEGER,
                        runtime_hours DECIMAL(5,2),
                        recorded_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(line_id, station_id, date, shift)
                    )
                """))
                
                # Check if table has data
                count = conn.execute(text("SELECT COUNT(*) FROM energy_consumption")).fetchone()[0]
                
                if count == 0:
                    # Generate sample data
                    conn.execute(text("""
                        INSERT INTO energy_consumption (line_id, station_id, date, shift, energy_kwh, peak_power_kw, units_produced, runtime_hours)
                        SELECT 
                            ls.line_id,
                            NULL as station_id,
                            ls.date,
                            ls.shift,
                            -- Energy based on production with some variation
                            (ls.total_units_produced * 0.05 + RANDOM() * 10 + 50)::DECIMAL(10,2) as energy_kwh,
                            -- Peak power
                            (30 + RANDOM() * 20)::DECIMAL(10,2) as peak_power_kw,
                            ls.total_units_produced,
                            ls.operating_time_min / 60.0 as runtime_hours
                        FROM oee_line_shift ls
                        WHERE ls.date >= :start_date AND ls.date <= :end_date
                        ON CONFLICT DO NOTHING
                    """), {'start_date': start_date, 'end_date': end_date})
                    conn.commit()
                
                # Get overview stats
                stats = conn.execute(text("""
                    SELECT 
                        SUM(energy_kwh) as total_energy,
                        AVG(energy_kwh) as avg_energy_per_shift,
                        MAX(peak_power_kw) as max_peak_power,
                        SUM(units_produced) as total_units,
                        ROUND(SUM(energy_kwh) / NULLIF(SUM(units_produced), 0)::DECIMAL, 4) as energy_per_unit,
                        COUNT(DISTINCT line_id) as active_lines
                    FROM energy_consumption
                    WHERE date >= :start_date AND date <= :end_date
                """), {'start_date': start_date, 'end_date': end_date}).fetchone()
                
                # Convert Decimal types to float/int for safe calculations
                if stats:
                    stats = type('obj', (object,), {
                        'total_energy': float(stats.total_energy or 0),
                        'avg_energy_per_shift': float(stats.avg_energy_per_shift or 0),
                        'max_peak_power': float(stats.max_peak_power or 0),
                        'total_units': int(stats.total_units or 0),
                        'energy_per_unit': float(stats.energy_per_unit or 0),
                        'active_lines': int(stats.active_lines or 0)
                    })()
        except Exception as e:
            with container:
                ui.label(f'Error loading energy data: {str(e)}').classes('text-red')
            return
        
        with container:
            with ui.card().classes('flex-1 bg-yellow-50'):
                with ui.column().classes('gap-1'):
                    ui.label(f'{stats.total_energy:,.0f} kWh').classes('text-3xl font-bold text-yellow-800')
                    ui.label('Total Energy Consumed').classes('text-sm text-grey-7')
                    ui.label(f'Last {days} days').classes('text-xs text-grey-6')
            
            with ui.card().classes('flex-1 bg-green-50'):
                with ui.column().classes('gap-1'):
                    ui.label(f'{stats.energy_per_unit:.4f} kWh').classes('text-3xl font-bold text-green-800')
                    ui.label('Energy per Unit').classes('text-sm text-grey-7')
                    ui.label('Average efficiency').classes('text-xs text-grey-6')
            
            with ui.card().classes('flex-1 bg-orange-50'):
                with ui.column().classes('gap-1'):
                    ui.label(f'{stats.max_peak_power:.1f} kW').classes('text-3xl font-bold text-orange-800')
                    ui.label('Peak Power Demand').classes('text-sm text-grey-7')
                    ui.label('Maximum recorded').classes('text-xs text-grey-6')
            
            with ui.card().classes('flex-1 bg-blue-50'):
                with ui.column().classes('gap-1'):
                    co2_saved = (float(stats.total_energy or 0) * 0.0004)  # Assuming efficiency improvements
                    ui.label(f'{co2_saved:.1f} kg').classes('text-3xl font-bold text-blue-800')
                    ui.label('CO₂ Reduction Potential').classes('text-sm text-grey-7')
                    ui.label('vs. baseline').classes('text-xs text-grey-6')
    
    def load_line_energy_comparison(container, days):
        """Load energy comparison by production line."""
        container.clear()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            with engine.connect() as conn:
                lines = conn.execute(text("""
                    SELECT 
                        ec.line_id,
                        ls.line_name,
                        SUM(ec.energy_kwh) as total_energy,
                        SUM(ec.units_produced) as total_units,
                        ROUND(SUM(ec.energy_kwh) / NULLIF(SUM(ec.units_produced), 0)::DECIMAL, 4) as energy_per_unit,
                        AVG(ec.energy_kwh) as avg_energy_per_shift,
                        MAX(ec.peak_power_kw) as max_peak_power
                    FROM energy_consumption ec
                    JOIN (SELECT DISTINCT line_id, line_name FROM oee_line_shift) ls ON ec.line_id = ls.line_id
                    WHERE ec.date >= :start_date AND ec.date <= :end_date
                    GROUP BY ec.line_id, ls.line_name
                    ORDER BY total_energy DESC
                """), {'start_date': start_date, 'end_date': end_date}).fetchall()
        except Exception as e:
            with container:
                ui.label(f'Error loading line data: {str(e)}').classes('text-red')
            return
        
        with container:
            if not lines:
                ui.label('No energy data available for the selected period.').classes('text-grey-6 italic')
            else:
                # Create table
                with ui.card().classes('w-full'):
                    ui.label('Energy Consumption by Production Line').classes('text-xl font-bold')
                    ui.separator()
                    
                    # Table header
                    with ui.row().classes('w-full font-bold bg-grey-2 p-2'):
                        ui.label('Line').classes('w-32')
                        ui.label('Total Energy').classes('w-32 text-right')
                        ui.label('Efficiency').classes('w-32 text-right')
                        ui.label('Peak Power').classes('w-32 text-right')
                        ui.label('Energy Chart').classes('flex-1')
                    
                    # Find max for scaling
                    max_energy = max(line.total_energy for line in lines)
                    
                    for line in lines:
                        energy_pct = (line.total_energy / max_energy * 100) if max_energy > 0 else 0
                        
                        # Determine efficiency color
                        if line.energy_per_unit < 0.05:
                            efficiency_color = 'green'
                        elif line.energy_per_unit < 0.08:
                            efficiency_color = 'orange'
                        else:
                            efficiency_color = 'red'
                        
                        with ui.row().classes('w-full items-center p-2 border-t'):
                            ui.label(line.line_name).classes('w-32 font-medium')
                            ui.label(f'{line.total_energy:,.0f} kWh').classes('w-32 text-right')
                            ui.badge(f'{line.energy_per_unit:.4f} kWh/unit', color=efficiency_color).classes('w-32')
                            ui.label(f'{line.max_peak_power:.1f} kW').classes('w-32 text-right')
                            
                            # Energy bar
                            with ui.column().classes('flex-1'):
                                with ui.row().classes('w-full items-center gap-2'):
                                    ui.linear_progress(value=energy_pct/100, size='20px').classes(f'flex-1').props(f'color=yellow-{7 if energy_pct > 70 else 6}')
                                    ui.label(f'{energy_pct:.0f}%').classes('text-xs text-grey-7')
    
    def load_energy_production_correlation(container, days):
        """Load correlation between energy and production."""
        container.clear()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            with engine.connect() as conn:
                correlation_data = conn.execute(text("""
                    SELECT 
                        ec.line_id,
                        ls.line_name,
                        ec.date,
                        ec.shift,
                        ec.energy_kwh,
                        ec.units_produced,
                        ROUND(ec.energy_kwh / NULLIF(ec.units_produced, 0)::DECIMAL, 4) as energy_efficiency,
                        ROUND(ec.energy_kwh / NULLIF(ec.runtime_hours, 0)::DECIMAL, 2) as power_consumption_rate
                    FROM energy_consumption ec
                    JOIN (SELECT DISTINCT line_id, line_name FROM oee_line_shift) ls ON ec.line_id = ls.line_id
                    WHERE ec.date >= :start_date AND ec.date <= :end_date
                    AND ec.units_produced > 0
                    ORDER BY ec.date DESC, ec.line_id, ec.shift
                    LIMIT 50
                """), {'start_date': start_date, 'end_date': end_date}).fetchall()
        except Exception as e:
            with container:
                ui.label(f'Error loading correlation data: {str(e)}').classes('text-red')
            return
        
        with container:
            if not correlation_data:
                ui.label('No correlation data available.').classes('text-grey-6 italic')
            else:
                with ui.card().classes('w-full'):
                    ui.label('Energy vs. Production Correlation').classes('text-xl font-bold')
                    ui.separator()
                    
                    ui.markdown("""
                    **Analysis:** This shows the relationship between energy consumption and production output.
                    Lower kWh/unit values indicate better energy efficiency.
                    """).classes('text-sm text-grey-7')
                    
                    # Group by line for analysis
                    from collections import defaultdict
                    line_data = defaultdict(list)
                    for row in correlation_data:
                        line_data[row.line_name].append({
                            'energy': float(row.energy_kwh),
                            'units': row.units_produced,
                            'efficiency': float(row.energy_efficiency) if row.energy_efficiency else 0
                        })
                    
                    # Display correlation insights per line
                    for line_name, data in line_data.items():
                        avg_efficiency = sum(d['efficiency'] for d in data) / len(data)
                        total_energy = sum(d['energy'] for d in data)
                        total_units = sum(d['units'] for d in data)
                        
                        # Calculate correlation strength (simplified)
                        efficiencies = [d['efficiency'] for d in data]
                        std_dev = (sum((e - avg_efficiency)**2 for e in efficiencies) / len(efficiencies))**0.5
                        consistency = 'High' if std_dev < 0.01 else 'Medium' if std_dev < 0.02 else 'Low'
                        
                        with ui.expansion(f'{line_name} - {avg_efficiency:.4f} kWh/unit avg', icon='insights').classes('w-full'):
                            with ui.row().classes('w-full gap-4'):
                                with ui.column().classes('flex-1'):
                                    ui.label(f'Total Energy: {total_energy:,.0f} kWh').classes('text-sm')
                                    ui.label(f'Total Production: {total_units:,} units').classes('text-sm')
                                    ui.label(f'Efficiency Consistency: {consistency}').classes('text-sm')
                                    ui.label(f'Standard Deviation: {std_dev:.4f}').classes('text-xs text-grey-6')
                                
                                with ui.column().classes('flex-1'):
                                    # Simple efficiency trend visualization
                                    recent_5 = efficiencies[-5:]
                                    if len(recent_5) >= 2:
                                        trend = '📈 Increasing' if recent_5[-1] > recent_5[0] else '📉 Improving' if recent_5[-1] < recent_5[0] else '➡️ Stable'
                                        ui.label(f'Recent Trend: {trend}').classes('text-sm font-medium')
                                    
                                    best_efficiency = min(efficiencies)
                                    worst_efficiency = max(efficiencies)
                                    ui.label(f'Best: {best_efficiency:.4f} kWh/unit').classes('text-sm text-green')
                                    ui.label(f'Worst: {worst_efficiency:.4f} kWh/unit').classes('text-sm text-red')
    
    def load_sustainability_metrics(container, days):
        """Load sustainability and environmental metrics."""
        container.clear()
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            with engine.connect() as conn:
                metrics = conn.execute(text("""
                    SELECT 
                        SUM(energy_kwh) as total_energy,
                        SUM(units_produced) as total_units,
                        COUNT(DISTINCT line_id) as active_lines,
                        COUNT(DISTINCT date) as operating_days
                    FROM energy_consumption
                    WHERE date >= :start_date AND date <= :end_date
                """), {'start_date': start_date, 'end_date': end_date}).fetchone()
        except Exception as e:
            with container:
                ui.label(f'Error loading sustainability metrics: {str(e)}').classes('text-red')
            return
        
        # Calculate sustainability metrics - ensure all values are float
        total_energy = float(metrics.total_energy or 0)
        total_units = int(metrics.total_units or 0)
        
        # CO2 emissions (average grid emission factor: 0.4 kg CO2/kWh)
        co2_emissions = total_energy * 0.4
        
        # Energy cost (assuming $0.12/kWh)
        energy_cost = total_energy * 0.12
        
        # Potential savings with 10% efficiency improvement
        potential_savings_energy = total_energy * 0.10
        potential_savings_cost = potential_savings_energy * 0.12
        potential_co2_reduction = potential_savings_energy * 0.4
        
        # Calculate renewable energy equivalent
        solar_panels_needed = math.ceil(total_energy / (days * 4)) if total_energy > 0 else 0  # Assuming 4 kWh per panel per day
        
        with container:
            with ui.row().classes('w-full gap-4'):
                # CO2 Emissions Card
                with ui.card().classes('flex-1 bg-red-50'):
                    ui.icon('cloud', size='lg').classes('text-red-700')
                    ui.label('Carbon Footprint').classes('text-lg font-bold')
                    ui.separator()
                    ui.label(f'{co2_emissions:,.1f} kg CO₂').classes('text-2xl font-bold text-red-700')
                    ui.label(f'Based on {total_energy:,.0f} kWh consumed').classes('text-xs text-grey-6')
                    ui.label(f'≈ {co2_emissions/1000:.2f} tons CO₂').classes('text-sm text-grey-7 mt-2')
                
                # Energy Cost Card
                with ui.card().classes('flex-1 bg-orange-50'):
                    ui.icon('attach_money', size='lg').classes('text-orange-700')
                    ui.label('Energy Cost').classes('text-lg font-bold')
                    ui.separator()
                    ui.label(f'${energy_cost:,.2f}').classes('text-2xl font-bold text-orange-700')
                    ui.label(f'${energy_cost/days:.2f} per day average').classes('text-xs text-grey-6')
                    ui.label(f'${energy_cost/total_units:.4f} per unit' if total_units > 0 else '$0').classes('text-sm text-grey-7 mt-2')
            
            # Improvement Potential Card
            with ui.card().classes('w-full bg-green-50 mt-4'):
                ui.label('💡 Efficiency Improvement Potential').classes('text-xl font-bold text-green-800')
                ui.separator()
                
                with ui.row().classes('w-full gap-4 mt-2'):
                    with ui.column().classes('flex-1'):
                        ui.label('With 10% Efficiency Improvement:').classes('font-medium')
                        ui.label(f'✓ Save {potential_savings_energy:,.0f} kWh energy').classes('text-sm')
                        ui.label(f'✓ Save ${potential_savings_cost:,.2f} in costs').classes('text-sm')
                        ui.label(f'✓ Reduce {potential_co2_reduction:,.1f} kg CO₂ emissions').classes('text-sm')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('Renewable Energy Equivalent:').classes('font-medium')
                        ui.label(f'☀️ {solar_panels_needed} solar panels needed').classes('text-sm')
                        ui.label(f'🌳 Equivalent to {int(co2_emissions/20)} trees planted').classes('text-sm')
                        ui.label(f'🚗 ≈ {int(co2_emissions/120)} gallons of gas saved').classes('text-sm')
            
            # Recommendations Card
            with ui.card().classes('w-full bg-blue-50 mt-4'):
                ui.label('📋 Sustainability Recommendations').classes('text-xl font-bold text-blue-800')
                ui.separator()
                
                with ui.column().classes('gap-2 mt-2'):
                    ui.label('✓ Implement peak-hour production scheduling to reduce demand charges').classes('text-sm')
                    ui.label('✓ Invest in energy-efficient equipment upgrades for high-consumption lines').classes('text-sm')
                    ui.label('✓ Install real-time energy monitoring on all stations').classes('text-sm')
                    ui.label('✓ Consider on-site renewable energy generation (solar/wind)').classes('text-sm')
                    ui.label('✓ Schedule maintenance during off-peak hours to optimize energy usage').classes('text-sm')
    
    # Main UI
    with ui.column().classes('w-full p-4 gap-4'):
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            with ui.column().classes('gap-1'):
                ui.label('Energy Consumption Tracking').classes('text-3xl font-bold')
                ui.label('Monitor power usage, efficiency, and sustainability metrics').classes('text-sm text-grey-7')
            with ui.row().classes('gap-2'):
                ui.icon('bolt', size='lg').classes('text-yellow-600')
                ui.icon('eco', size='lg').classes('text-green-600')
        
        # Time period filter
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full gap-4 items-end'):
                days_filter = ui.select(
                    [7, 14, 30, 60, 90],
                    label='Time Period (days)',
                    value=30
                ).classes('w-48')
                
                ui.button(
                    'Refresh Data',
                    icon='refresh',
                    on_click=lambda: refresh_all_data()
                ).classes('bg-primary')
        
        # Energy Overview
        energy_overview = ui.row().classes('w-full gap-4')
        
        # Line Energy Comparison
        with ui.card().classes('w-full mt-4'):
            ui.label('Energy by Production Line').classes('text-2xl font-bold')
            ui.separator()
            line_energy = ui.column().classes('w-full gap-2')
        
        # Tabs for detailed analysis
        with ui.tabs().classes('w-full mt-4') as tabs:
            tab_correlation = ui.tab('Energy-Production Correlation', icon='scatter_plot')
            tab_sustainability = ui.tab('Sustainability Metrics', icon='eco')
        
        with ui.tab_panels(tabs, value=tab_correlation).classes('w-full'):
            with ui.tab_panel(tab_correlation):
                correlation_container = ui.column().classes('w-full gap-2')
            
            with ui.tab_panel(tab_sustainability):
                sustainability_container = ui.column().classes('w-full gap-2')
        
        # Load initial data
        def refresh_all_data():
            load_energy_overview(energy_overview, days_filter.value)
            load_line_energy_comparison(line_energy, days_filter.value)
            load_energy_production_correlation(correlation_container, days_filter.value)
            load_sustainability_metrics(sustainability_container, days_filter.value)
            ui.notify('Data refreshed', type='positive')
        
        refresh_all_data()
