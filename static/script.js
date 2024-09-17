function formatDate(dateStr) {
    const date = new Date(dateStr);
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric', timeZone: 'UTC' };
    return date.toLocaleString('en-GB', options) + ' UTC';
}

function fetchEvents() {
    fetch('/events')
        .then(response => response.json())
        .then(data => {
            const eventsList = document.getElementById('events-list');
            eventsList.innerHTML = '';  // Clear previous list

            data.forEach(event => {
                const tr = document.createElement('tr');

                const usernameTd = document.createElement('td');
                usernameTd.textContent = event.author;

                const actionTd = document.createElement('td');
                let actionText = '';

                if (event.action === 'PUSH') {
                    actionText = `pushed to ${event.to_branch}`;
                } else if (event.action === 'PULL_REQUEST') {
                    actionText = `submitted a pull request from ${event.from_branch} to ${event.to_branch}`;
                } else if (event.action === 'MERGE') {
                    actionText = `merged branch ${event.from_branch} to ${event.to_branch}`;
                }

                actionTd.textContent = actionText;

                const explanationTd = document.createElement('td');
                explanationTd.textContent = actionText;

                const timeTd = document.createElement('td');
                timeTd.textContent = formatDate(event.timestamp);

                tr.appendChild(usernameTd);
                tr.appendChild(actionTd);
                tr.appendChild(explanationTd);
                tr.appendChild(timeTd);

                eventsList.appendChild(tr);
            });
        })
        .catch(error => console.error('Error fetching events:', error));
}

// Poll every 15 seconds
setInterval(fetchEvents, 15000);

// Initial load
fetchEvents();
