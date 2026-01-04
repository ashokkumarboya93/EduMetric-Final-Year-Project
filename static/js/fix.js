// Update KPIs for group analytics
function updateCanvasKPIs(stats) {
    const kpisContainer = document.getElementById('canvas-kpis');
    if (!kpisContainer || !stats) return;
    
    kpisContainer.innerHTML = '';
    
    const kpiData = [
        { label: 'Total Students', value: stats.total_students || 0, icon: 'fa-users', class: 'kpi-info' },
        { label: 'Average Performance', value: `${(stats.avg_performance || 0).toFixed(1)}%`, icon: 'fa-chart-line', class: 'kpi-primary' },
        { label: 'High Performers', value: stats.high_performers || 0, icon: 'fa-star', class: 'kpi-success' },
        { label: 'High Risk', value: stats.high_risk || 0, icon: 'fa-triangle-exclamation', class: 'kpi-warning' },
        { label: 'High Dropout', value: stats.high_dropout || 0, icon: 'fa-user-xmark', class: 'kpi-danger' }
    ];
    
    kpiData.forEach(kpi => {
        const kpiDiv = document.createElement('div');
        kpiDiv.className = `canvas-kpi ${kpi.class}`;
        kpiDiv.innerHTML = `
            <h4><i class="fa-solid ${kpi.icon}"></i> ${kpi.label}</h4>
            <div class="value">${kpi.value}</div>
        `;
        kpisContainer.appendChild(kpiDiv);
    });
}