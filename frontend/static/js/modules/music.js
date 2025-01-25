// frontend/static/js/music.js
export function initializeMusicPlayer() {
    const apiEndpoint = '/api/music';

    let currentLevel = 'genre';
    let selectedGenre = '';
    let selectedAlbum = '';
    let songList = []; // To store the list of songs for the current album
    let currentSongIndex = -1; // Tracks the current song index

    function populateDropdown(options, level) {
        const dropdown = document.getElementById('dynamic-selector');
        if (!dropdown) {
            console.error('Dropdown element not found.');
            return;
        }

        dropdown.innerHTML = '';

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = `Select a ${level}`;
        placeholder.disabled = true;
        placeholder.selected = true;
        dropdown.appendChild(placeholder);

        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            dropdown.appendChild(opt);
        });

        currentLevel = level;
    }

    function showBackButton() {
        const backButton = document.getElementById('back-button');
        if (backButton) {
            backButton.style.display = 'block';
        }
    }

    function hideBackButton() {
        const backButton = document.getElementById('back-button');
        if (backButton) {
            backButton.style.display = 'none';
        }
    }

    function handleBack() {
        if (currentLevel === 'album') {
            fetchOptions(apiEndpoint).then(data => {
                if (data && data.genres) {
                    populateDropdown(data.genres, 'genre');
                    selectedGenre = '';
                    selectedAlbum = '';
                    hideBackButton();
                }
            });
        } else if (currentLevel === 'song') {
            fetchOptions(`${apiEndpoint}/${selectedGenre}`).then(data => {
                if (data && data.albums) {
                    populateDropdown(data.albums, 'album');
                    selectedAlbum = '';
                    showBackButton();
                }
            });
        }
    }

    async function fetchOptions(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }
            const data = await response.json();
            if (data.success) {
                return data;
            } else {
                console.error('Error:', data.message);
                return null;
            }
        } catch (error) {
            console.error('Fetch error:', error.message);
            return null;
        }
    }

    // Play song
    function playSong(index) {
        const audioPlayer = document.getElementById('audio-player');
        const audioSource = document.getElementById('audio-source');
        const nowPlaying = document.getElementById('current-song');

        if (!audioPlayer || !audioSource || !songList[index]) {
            console.error('Error: Audio player, source, or song not found.');
            return;
        }

        currentSongIndex = index; // Update the current song index
        const songPath = `/static/assets/sounds/${selectedGenre}/${selectedAlbum}/${songList[currentSongIndex]}`;

        console.log('Playing song:', songPath);
        nowPlaying.textContent = `${songList[currentSongIndex]}`; // Update "Now Playing" text

        audioSource.src = songPath;
        audioPlayer.pause(); // Pause any current playback
        audioPlayer.load(); // Load the new song
        audioPlayer.addEventListener(
            'canplaythrough',
            () => {
                audioPlayer.play().catch(error => {
                    console.error('Error while trying to play the song:', error);
                });
            },
            { once: true }
        );

        // Automatically play the next song when the current one ends
        audioPlayer.onended = () => {
            if (currentSongIndex < songList.length - 1) {
                playSong(currentSongIndex + 1);
            } else {
                console.log('Reached the last song in the album.');
            }
        };
    }

    async function handleSelection(event) {
        const selectedValue = event.target.value;

        if (currentLevel === 'genre') {
            selectedGenre = selectedValue;
            const albums = await fetchOptions(`${apiEndpoint}/${selectedGenre}`);
            if (albums && albums.albums) {
                populateDropdown(albums.albums, 'album');
                showBackButton();
            }
        } else if (currentLevel === 'album') {
            selectedAlbum = selectedValue;
            const songs = await fetchOptions(`${apiEndpoint}/${selectedGenre}/${selectedAlbum}`);
            if (songs && songs.songs) {
                populateDropdown(songs.songs, 'song');
                songList = songs.songs; // Update the global song list
                currentSongIndex = -1; // Reset the current song index
            }
        } else if (currentLevel === 'song') {
            const selectedIndex = songList.findIndex(song => song === selectedValue);

            if (selectedIndex !== -1) {
                playSong(selectedIndex); // Play the selected song
            } else {
                console.error('Selected song not found in the list.');
            }
        }
    }

    function setupEventListeners() {
        const dropdown = document.getElementById('dynamic-selector');
        if (!dropdown) {
            console.error('Dropdown element not found.');
            return;
        }
        dropdown.addEventListener('change', handleSelection);

        const backButton = document.getElementById('back-button');
        if (backButton) {
            backButton.addEventListener('click', handleBack);
        }

        const prevTrackButton = document.getElementById('prev-track');
        const nextTrackButton = document.getElementById('next-track');

        if (prevTrackButton) {
            prevTrackButton.addEventListener('click', () => {
                if (currentSongIndex > 0) {
                    playSong(currentSongIndex - 1);
                } else {
                    console.log('Already at the first song.');
                }
            });
        }

        if (nextTrackButton) {
            nextTrackButton.addEventListener('click', () => {
                if (currentSongIndex < songList.length - 1) {
                    playSong(currentSongIndex + 1);
                } else {
                    console.log('Already at the last song.');
                }
            });
        }
    }

    async function initialize() {
        const genres = await fetchOptions(apiEndpoint);
        if (genres && genres.genres) {
            populateDropdown(genres.genres, 'genre');
            setupEventListeners();
        }
    }

    initialize();
}