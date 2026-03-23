document.addEventListener("DOMContentLoaded", function () {
    const monthEl = document.getElementById("month");
    const datesEl = document.getElementById("dates");
    const prevBtn = document.getElementById("prev");
    const nextBtn = document.getElementById("next");
    const taskBox = document.getElementById("taskBox");
    const selectedDateEl = document.getElementById("selectedDate");
    const taskInput = document.getElementById("taskInput");
    const taskList = document.getElementById("taskList");

    if (!monthEl || !datesEl || !prevBtn || !nextBtn) {
        return;
    }

    let currentDate = new Date();
    let selectedDateKey = "";

    const monthNames = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    function renderCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        const firstDay = new Date(year, month, 1).getDay();
        const lastDate = new Date(year, month + 1, 0).getDate();

        monthEl.textContent = `${monthNames[month]} ${year}`;
        datesEl.innerHTML = "";

        for (let i = 0; i < firstDay; i++) {
            const emptyCell = document.createElement("div");
            emptyCell.classList.add("date", "empty");
            datesEl.appendChild(emptyCell);
        }

        const today = new Date();

        for (let day = 1; day <= lastDate; day++) {
            const cell = document.createElement("div");
            cell.classList.add("date");
            cell.textContent = day;

            const dateKey = `${year}-${month + 1}-${day}`;

            if (
                day === today.getDate() &&
                month === today.getMonth() &&
                year === today.getFullYear()
            ) {
                cell.classList.add("today");
            }

            const savedTasks = localStorage.getItem(`calendar_tasks_${dateKey}`);
            if (savedTasks) {
                cell.classList.add("has-task");
            }

            cell.addEventListener("click", function () {
                document.querySelectorAll(".date").forEach(d => d.classList.remove("active"));
                cell.classList.add("active");

                selectedDateKey = dateKey;

                if (selectedDateEl) {
                    selectedDateEl.textContent = `Tasks for ${day} ${monthNames[month]} ${year}`;
                }

                if (taskBox) {
                    taskBox.style.display = "block";
                }

                renderTaskList();
            });

            datesEl.appendChild(cell);
        }
    }

    function renderTaskList() {
        if (!taskList) return;

        taskList.innerHTML = "";
        let tasks = JSON.parse(localStorage.getItem(`calendar_tasks_${selectedDateKey}`)) || [];

        tasks.forEach((task, index) => {
            const li = document.createElement("li");
            li.textContent = task;

            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "Delete";
            deleteBtn.style.marginLeft = "10px";
            deleteBtn.style.padding = "4px 8px";
            deleteBtn.style.border = "none";
            deleteBtn.style.borderRadius = "6px";
            deleteBtn.style.cursor = "pointer";

            deleteBtn.addEventListener("click", function () {
                tasks.splice(index, 1);
                localStorage.setItem(`calendar_tasks_${selectedDateKey}`, JSON.stringify(tasks));
                renderTaskList();
                renderCalendar();
            });

            li.appendChild(deleteBtn);
            taskList.appendChild(li);
        });
    }

    window.saveTask = function () {
        if (!selectedDateKey || !taskInput) return;

        const task = taskInput.value.trim();
        if (!task) return;

        let tasks = JSON.parse(localStorage.getItem(`calendar_tasks_${selectedDateKey}`)) || [];
        tasks.push(task);
        localStorage.setItem(`calendar_tasks_${selectedDateKey}`, JSON.stringify(tasks));

        taskInput.value = "";
        renderTaskList();
        renderCalendar();
    };

    prevBtn.addEventListener("click", function () {
        datesEl.classList.add("fade-out");

        setTimeout(() => {
            currentDate.setMonth(currentDate.getMonth() - 1);
            renderCalendar();
            datesEl.classList.remove("fade-out");
            datesEl.classList.add("fade-in");

            setTimeout(() => {
                datesEl.classList.remove("fade-in");
            }, 250);
        }, 200);
    });

    nextBtn.addEventListener("click", function () {
        datesEl.classList.add("fade-out");

        setTimeout(() => {
            currentDate.setMonth(currentDate.getMonth() + 1);
            renderCalendar();
            datesEl.classList.remove("fade-out");
            datesEl.classList.add("fade-in");

            setTimeout(() => {
                datesEl.classList.remove("fade-in");
            }, 250);
        }, 200);
    });

    renderCalendar();
});