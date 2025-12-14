   
   /* ===========================================================
      GROUP ANALYTICS (DEPT / YEAR / COLLEGE)
      =========================================================== */
   
   function fillGroupTable(tableId, rows, includeDept = false) {
       const tbody = document.querySelector(`#${tableId} tbody`);
       tbody.innerHTML = "";
   
       rows.forEach(r => {
           const tr = document.createElement("tr");
           tr.innerHTML = `
               <td>${r.RNO}</td>
               <td>${r.NAME}</td>
               ${includeDept ? `<td>${r.DEPT}</td>` : ""}
               <td>${r.YEAR}</td>
               <td>${r.CURR_SEM}</td>
               <td>${r.performance_label}</td>
               <td>${r.risk_label}</td>
               <td>${r.dropout_label}</td>
               <td>${r.performance_overall.toFixed(1)}</td>
               <td>${r.risk_score.toFixed(1)}</td>
               <td>${r.dropout_score.toFixed(1)}</td>
           `;
           tbody.appendChild(tr);
       });
   }
   
   /* PIE CHART (labels) */
   function renderLabelDonut(elementId, counts, title) {
       Plotly.newPlot(elementId, [{
           labels: Object.keys(counts),
           values: Object.values(counts),
           type: "pie",
           hole: 0.4
       }], {
           title,
           paper_bgcolor: "rgba(255,255,255,0)"
       }, { displayModeBar: false });
   }
   
   /* 3D CHART */
   function render3DScatter(elementId, scores, title) {
       Plotly.newPlot(elementId, [{
           x: scores.performance,
           y: scores.risk,
           z: scores.dropout,
           mode: "markers",
           type: "scatter3d",
           marker: { size: 3 }
       }], {
           title,
           scene: {
               xaxis: { title: "Performance" },
               yaxis: { title: "Risk" },
               zaxis: { title: "Dropout" }
           },
           paper_bgcolor: "rgba(255,255,255,0)"
       }, { displayModeBar: false });
   }
   
   /* ===========================================================
      DEPARTMENT ANALYTICS
      =========================================================== */
   async function analyseDepartment() {
       const payload = {
           dept: document.getElementById("d-dept").value,
           year: document.getElementById("d-year").value
       };
   
       showLoading("Analysing department...");
       const res = await api("/api/department/analyze", "POST", payload);
       hideLoading();
   
       if (!res.success) {
           alert(res.message || "Department analysis failed");
           return;
       }
   
       document.getElementById("dept-report").classList.remove("hidden");
   
       const st = res.stats;
       document.getElementById("dept-kpi-total").innerHTML =
           `👥 Total Students<br><b>${st.total_students}</b>`;
       document.getElementById("dept-kpi-high-perf").innerHTML =
           `🎓 High Performers<br><b>${st.high_performers}</b>`;
       document.getElementById("dept-kpi-high-risk").innerHTML =
           `⚠️ High Risk<br><b>${st.high_risk}</b>`;
       document.getElementById("dept-kpi-high-drop").innerHTML =
           `🚨 High Dropout<br><b>${st.high_dropout}</b>`;
   
       fillGroupTable("dept-table", res.table.slice(0, 120));
   
       renderLabelDonut("dept-chart-perf-donut", res.label_counts.performance, "Performance Distribution");
       renderLabelDonut("dept-chart-risk-donut", res.label_counts.risk, "Risk Distribution");
       renderLabelDonut("dept-chart-drop-donut", res.label_counts.dropout, "Dropout Distribution");
       render3DScatter("dept-chart-3d", res.scores, "3D Performance-Risk-Dropout");
   
       document.getElementById("dept-summary").innerHTML = `
           <p>Total students analysed: <b>${st.total_students}</b></p>
           <p>Avg Performance: <b>${st.avg_performance}%</b></p>
           <p>High performers: <b>${st.high_performers}</b> • High risk: <b>${st.high_risk}</b> • High dropout: <b>${st.high_dropout}</b></p>
       `;
   }
   
   /* ===========================================================
      YEAR ANALYTICS
      =========================================================== */
   async function analyseYear() {
       const payload = { year: document.getElementById("y-year").value };
   
       showLoading("Analysing year...");
       const res = await api("/api/year/analyze", "POST", payload);
       hideLoading();
   
       if (!res.success) {
           alert(res.message || "Year analysis failed");
           return;
       }
   
       document.getElementById("year-report").classList.remove("hidden");
   
       const st = res.stats;
       document.getElementById("year-kpi-total").innerHTML =
           `👥 Total Students<br><b>${st.total_students}</b>`;
       document.getElementById("year-kpi-avg-perf").innerHTML =
           `📈 Avg Performance<br><b>${st.avg_performance}%</b>`;
       document.getElementById("year-kpi-high-risk").innerHTML =
           `⚠️ High Risk<br><b>${st.high_risk}</b>`;
       document.getElementById("year-kpi-high-drop").innerHTML =
           `🚨 High Dropout<br><b>${st.high_dropout}</b>`;
   
       fillGroupTable("year-table", res.table.slice(0, 120), true);
   
       renderLabelDonut("year-chart-perf-donut", res.label_counts.performance, "Performance Labels");
       render3DScatter("year-chart-3d", res.scores, "3D Performance-Risk-Dropout");
   
       Plotly.newPlot("year-chart-box", [{
           y: res.scores.performance,
           type: "box",
           name: "Performance"
       }], {
           title: "Performance Spread",
           paper_bgcolor: "rgba(255,255,255,0)"
       }, { displayModeBar: false });
   
       Plotly.newPlot("year-chart-hist", [{
           x: res.scores.performance,
           type: "histogram"
       }], {
           title: "Performance Distribution Histogram",
           paper_bgcolor: "rgba(255,255,255,0)"
       }, { displayModeBar: false });
   
       document.getElementById("year-summary").innerHTML = `
           <p>Total students: <b>${st.total_students}</b></p>
           <p>Avg Performance: <b>${st.avg_performance}%</b></p>
       `;
   }
   
   /* ===========================================================
      COLLEGE ANALYTICS
      =========================================================== */
   async function analyseCollege() {
       showLoading("Analysing college...");
       const res = await api("/api/college/analyze", "GET");
       hideLoading();
   
       if (!res.success) {
           alert(res.message || "College analysis failed");
           return;
       }
   
       document.getElementById("college-report").classList.remove("hidden");
   
       const st = res.stats;
   
       document.getElementById("clg-kpi-total").innerHTML =
           `👥 Sample Size<br><b>${res.sample_size}</b>`;
       document.getElementById("clg-kpi-avg-perf").innerHTML =
           `📈 Avg Performance<br><b>${st.avg_performance}%</b>`;
       document.getElementById("clg-kpi-high-risk").innerHTML =
           `⚠️ High Risk<br><b>${st.high_risk}</b>`;
       document.getElementById("clg-kpi-high-drop").innerHTML =
           `🚨 High Dropout<br><b>${st.high_dropout}</b>`;
   
       fillGroupTable("clg-table", res.table.slice(0, 150), true);
   
       renderLabelDonut("clg-chart-perf-donut", res.label_counts.performance, "Performance");
       renderLabelDonut("clg-chart-risk-donut", res.label_counts.risk, "Risk");
       render3DScatter("clg-chart-3d", res.scores, "3D College Analysis");
   
       Plotly.newPlot("clg-chart-box", [{
           y: res.scores.performance,
           type: "box"
       }], {
           title: "Performance Spread Boxplot",
           paper_bgcolor: "rgba(255,255,255,0)"
       }, { displayModeBar: false });
   
       document.getElementById("clg-summary").innerHTML = `
           <p>Sample students: <b>${res.sample_size}</b></p>
           <p>Avg performance: <b>${st.avg_performance}%</b></p>
       `;
   }

   /* ===========================================================
      EXPORT FUNCTIONS FOR GROUP ANALYTICS
      =========================================================== */
   function exportDeptCSV() {
       alert("Department CSV export functionality - implement backend endpoint");
   }

   function exportYearCSV() {
       alert("Year CSV export functionality - implement backend endpoint");
   }

   function exportCollegeCSV() {
       alert("College CSV export functionality - implement backend endpoint");
   }

   /* ===========================================================
      BATCH MODE TOGGLE FUNCTIONALITY
      =========================================================== */
   let currentBatchMode = 'normalize';
   let selectedFileNormalize = null;

   function switchBatchMode(mode) {
       currentBatchMode = mode;
       
       document.getElementById('btn-normalize').classList.toggle('active', mode === 'normalize');
       document.getElementById('btn-analytics').classList.toggle('active', mode === 'analytics');
       
       document.getElementById('normalize-content').classList.toggle('hidden', mode !== 'normalize');
       document.getElementById('analytics-content').classList.toggle('hidden', mode !== 'analytics');
       
       resetBatchUpload();
   }

   function resetBatchUpload() {
       selectedFileNormalize = null;
       document.getElementById('batch-file-normalize').value = '';
       document.getElementById('upload-btn-normalize').disabled = true;
       document.getElementById('upload-status-normalize').classList.add('hidden');
       document.getElementById('batch-result').classList.add('hidden');
       document.getElementById('analytics-preview').classList.add('hidden');
   }

   window.addEventListener("DOMContentLoaded", () => {
       setupNormalizeUpload();
   });

   function setupNormalizeUpload() {
       const uploadArea = document.getElementById('upload-area-normalize');
       const fileInput = document.getElementById('batch-file-normalize');

       uploadArea.addEventListener("dragover", (e) => {
           e.preventDefault();
           uploadArea.classList.add("dragover");
       });

       uploadArea.addEventListener("dragleave", () => {
           uploadArea.classList.remove("dragover");
       });

       uploadArea.addEventListener("drop", (e) => {
           e.preventDefault();
           uploadArea.classList.remove("dragover");
           if (e.dataTransfer.files.length > 0) {
               handleNormalizeFileSelection(e.dataTransfer.files[0]);
           }
       });

       fileInput.addEventListener("change", (e) => {
           if (e.target.files.length > 0) {
               handleNormalizeFileSelection(e.target.files[0]);
           }
       });
   }

   function handleNormalizeFileSelection(file) {
       const statusDiv = document.getElementById('upload-status-normalize');
       const statusText = document.getElementById('status-text-normalize');
       const uploadBtn = document.getElementById('upload-btn-normalize');

       if (!file.name.endsWith(".csv") && !file.name.endsWith(".xlsx")) {
           statusDiv.classList.remove("hidden");
           statusText.textContent = "Invalid file type. Please select CSV or XLSX file.";
           statusDiv.style.background = "#ffebee";
           statusDiv.style.color = "#c62828";
           uploadBtn.disabled = true;
           return;
       }

       selectedFileNormalize = file;
       statusDiv.classList.remove("hidden");
       statusText.textContent = `File selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
       statusDiv.style.background = "#e3f2fd";
       statusDiv.style.color = "#0d47a1";
       uploadBtn.disabled = false;
   }

   async function uploadBatchFile(mode) {
       if (!selectedFileNormalize) {
           alert("Please select a file first.");
           return;
       }

       const formData = new FormData();
       formData.append("file", selectedFileNormalize);
       formData.append("mode", mode);

       showLoading("Normalizing data and generating predictions...");

       try {
           const response = await fetch("/api/batch-upload", {
               method: "POST",
               body: formData
           });

           const result = await response.json();
           hideLoading();

           if (result.success) {
               document.getElementById("batch-result").classList.remove("hidden");
               
               if (mode === 'normalize') {
                   document.getElementById("batch-processed-count").innerHTML = 
                       `📊 Added<br><b>${result.added || 0}</b>`;
                   document.getElementById("batch-total-count").innerHTML = 
                       `👥 Total Records<br><b>${result.total_records || 0}</b>`;
                   document.getElementById("batch-alerts-sent").innerHTML = 
                       `📧 Updated<br><b>${result.updated || 0}</b>`;
                   
                   alert(`✅ Normalization Complete! Added ${result.added || 0} new students, updated ${result.updated || 0} existing students.`);
               } else {
                   document.getElementById("batch-processed-count").innerHTML = 
                       `📊 Processed<br><b>${result.processed_rows || 0}</b>`;
                   document.getElementById("batch-total-count").innerHTML = 
                       `👥 Total Students<br><b>${result.total_students || 0}</b>`;
                   document.getElementById("batch-alerts-sent").innerHTML = 
                       `✅ Success<br><b>Complete</b>`;
                   
                   alert(`✅ Analytics Processing Complete! Processed ${result.processed_rows || 0} records.`);
               }
               
               document.getElementById("batch-message-text").textContent = result.message;

               await loadInitialStats();
               resetBatchUpload();
           } else {
               alert(`❌ Upload failed: ${result.message}`);
           }
       } catch (error) {
           hideLoading();
           console.error("Upload error:", error);
           alert("❌ Upload failed due to network error.");
       }
   }

   function showAnalyticsAfterNormalize() {
       switchBatchMode('analytics');
       loadAnalyticsDashboard();
   }

   async function loadAnalyticsDashboard() {
       showLoading("Loading analytics dashboard...");
       
       try {
           const result = await api("/api/analytics/preview", "GET");
           hideLoading();

           if (result.success) {
               document.getElementById('analytics-preview').classList.remove('hidden');
               
               document.getElementById('analytics-total-students').innerHTML = 
                   `👥 Total Students<br><b>${result.stats.total_students}</b>`;
               document.getElementById('analytics-high-risk').innerHTML = 
                   `⚠️ High Risk<br><b>${result.stats.high_risk}</b>`;
               document.getElementById('analytics-high-dropout').innerHTML = 
                   `🚨 High Dropout<br><b>${result.stats.high_dropout}</b>`;

               const tbody = document.querySelector('#analytics-table tbody');
               tbody.innerHTML = '';
               
               result.students.slice(0, 50).forEach(student => {
                   const tr = document.createElement('tr');
                   tr.innerHTML = `
                       <td>${student.RNO}</td>
                       <td>${student.NAME}</td>
                       <td>${student.DEPT}</td>
                       <td>${student.YEAR}</td>
                       <td><span class="label-${student.performance_label}">${student.performance_label}</span></td>
                       <td><span class="label-${student.risk_label}">${student.risk_label}</span></td>
                       <td><span class="label-${student.dropout_label}">${student.dropout_label}</span></td>
                       <td><button class="secondary-btn" onclick="viewStudentAnalytics('${student.RNO}')" style="padding: 4px 8px; font-size: 12px;">View Analytics</button></td>
                   `;
                   tbody.appendChild(tr);
               });
           } else {
               document.getElementById('analytics-preview').classList.add('hidden');
               alert(result.message || "No analytics data available");
           }
       } catch (error) {
           hideLoading();
           console.error("Analytics dashboard error:", error);
           alert("Failed to load analytics dashboard.");
       }
   }

   async function viewStudentAnalytics(rno) {
       try {
           const result = await api("/api/student/search", "POST", { rno });
           if (result.success) {
               currentStudent = result.student;
               await analyseStudent(currentStudent);
               
               // Switch to student mode
               document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
               document.querySelector('[data-mode="student"]').classList.add('active');
               
               document.querySelectorAll('.mode-section').forEach(sec => {
                   sec.classList.remove('active');
                   sec.classList.add('hidden');
               });
               
               document.getElementById('mode-student').classList.remove('hidden');
               document.getElementById('mode-student').classList.add('active');
           }
       } catch (error) {
           alert("Failed to load student analytics.");
       }
   }