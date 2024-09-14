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
                const li = document.createElement('li');
                let eventText = '';

                const formattedTimestamp = formatDate(event.timestamp);

                if (event.action === 'PUSH') {
                    eventText = `${event.author} pushed to ${event.to_branch} on ${formattedTimestamp}`;
                } else if (event.action === 'PULL_REQUEST') {
                    eventText = `${event.author} submitted a pull request from ${event.from_branch} to ${event.to_branch} on ${formattedTimestamp}`;
                } else if (event.action === 'MERGE') {
                    eventText = `${event.author} merged branch ${event.from_branch} to ${event.to_branch} on ${formattedTimestamp}`;
                }

                li.innerHTML = `<strong>${eventText}</strong>`;
                eventsList.appendChild(li);
            });
        })
        .catch(error => console.error('Error fetching events:', error));
}

// Poll every 15 seconds
setInterval(fetchEvents, 15000);

// Initial load
fetchEvents();
