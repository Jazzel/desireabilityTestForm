let currentPage = 1;
const totalFormPages = 19;
const formData = {
    personalInfo: {},
    responses: {}
};

// Frustration rating variables
const frustrationTitles = [
    "No event buddies",
    "Stuck in a social rut",
    "Struggling with starting conversations",
    "Difficulty finding people with similar interests",
    "No plans on short notice",
    "Feeling isolated in a new place"
];

let frustrationRatings = Array(6).fill(0);

// Define response pages configuration
const responsePages = {
    5: {
        name: "weekend",
        title: "What's Your Ideal Weekend?",
        options: 5  // 5 options
    },
    6: {
        name: "meeting",
        title: "How do you feel about meeting new people on app?",
        options: 5  // 5 options
    },
    7: {
        name: "vibe",
        title: "Pick your vibe.",
        options: 7  // 7 options
    },
    9: {
        name: "new_things",
        title: "When was the last time you tried something new with someone?",
        options: 3,  // 3 options (radio buttons)
        type: "radio"
    },
    10: {
        name: "frustrations",
        title: "Rate your frustration with these struggles",
        options: 6  // 6 frustration items
    },
    11: {
        name: "blockers",
        title: "What stopped you from meeting new people?",
        options: 6  // 6 options
    },
    13: {
        name: "safe_fun",
        title: "Would you try a SAFE, fun way to...?",
        options: 4  // 4 options
    },
    14: {
        name: "platform",
        title: "How likely are you to join a platform that helps you:",
        options: 5  // 5 options
    },
    15: {
        name: "challenges",
        title: "What are the biggest challenges you face when trying to meet new people or plan outings?",
        options: 5  // 5 options
    },
    16: {
        name: "features",
        title: "What features would you find most useful in an app that connects you with like-minded people?",
        options: 7  // 7 options
    },
    17: {
        name: "safety",
        title: "What safety features would make you feel more comfortable meeting strangers through an app?",
        options: 4  // 4 options
    },
    18: {
        name: "scenarios",
        title: "Which of these scenarios would you most likely use the app for?",
        options: 5  // 5 options
    }
};

// Function to calculate max selections based on option count
function getMaxSelections(optionCount) {
    if (optionCount >= 6) return 4;   // 7-6 options: max 4
    if (optionCount === 5) return 3;   // 5 options: max 3
    if (optionCount === 4) return 2;   // 4 options: max 2
    return 2;                          // Default: max 2
}

// Function to get page config by group name
function getPageConfigByGroupName(groupName) {
    for (const key in responsePages) {
        if (responsePages[key].name === groupName) {
            return responsePages[key];
        }
    }
    return null;
}

// Initialize first page as active
document.getElementById(`page${currentPage}`).classList.add("active");

// Email validation function
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Phone validation function
function validatePhone(phone) {
    return phone.length >= 7;
}

// Navigation Functions
function nextPage(pageNum) {
    if (validateCurrentPage()) {
        saveFormData();
        document.getElementById(`page${currentPage}`).classList.remove("active");
        document.getElementById(`page${pageNum}`).classList.add("active");
        currentPage = pageNum;
        updateProgress();
        window.scrollTo(0, 0);
    }
}

function prevPage(pageNum) {
    document.getElementById(`page${currentPage}`).classList.remove("active");
    document.getElementById(`page${pageNum}`).classList.add("active");
    currentPage = pageNum;
    updateProgress();
    window.scrollTo(0, 0);
}

// Progress Bar Update
function updateProgress() {
    const progress = (currentPage / totalFormPages) * 100;
    document.getElementById("progress-bar").style.width = `${progress}%`;
}

// Reset error states
function resetErrorStates() {
    document.querySelectorAll(".has-error").forEach((el) => {
        el.classList.remove("has-error");
    });
    document.querySelectorAll(".error-message").forEach((el) => {
        el.style.display = "none";
    });
}

// Form Validation
function validateCurrentPage() {
    resetErrorStates();
    let isValid = true;

    // Page 4 validation
    if (currentPage === 4) {
        const name = document.getElementById("fullName")?.value.trim();
        const gender = document.getElementById("gender")?.value;
        const age = document.getElementById("age")?.value;
        const city = document.getElementById("city")?.value;
        const email = document.getElementById("email")?.value.trim();
        const occupation = document.getElementById("occupation")?.value;
        // const phone = document.getElementById("phone")?.value.trim();

        // if (!name) {
        //     document.getElementById("fullName").classList.add("has-error");
        //     document.getElementById("name-error").style.display = "block";
        //     isValid = false;
        // }
        // if (!gender || gender === "") {
        //     document.getElementById("gender").classList.add("has-error");
        //     document.getElementById("gender-error").style.display = "block";
        //     isValid = false;
        // }
        // if (!age || age === "") {
        //     document.getElementById("age").classList.add("has-error");
        //     document.getElementById("age-error").style.display = "block";
        //     isValid = false;
        // }
        // if (!city || city === "") {
        //     document.getElementById("city").classList.add("has-error");
        //     document.getElementById("city-error").style.display = "block";
        //     isValid = false;
        // }
        // if (!email || !validateEmail(email)) {
        //     document.getElementById("email").classList.add("has-error");
        //     document.getElementById("email-error").style.display = "block";
        //     isValid = false;
        // }
        // if (phone && !validatePhone(phone)) {
        //     document.getElementById("phone").classList.add("has-error");
        //     document.getElementById("phone-error").style.display = "block";
        //     isValid = false;
        // }
        // if (!occupation || occupation === "") {
        //     document.getElementById("occupation").classList.add("has-error");
        //     document.getElementById("occupation-error").style.display = "block";
        //     isValid = false;
        // }
    }

    // Modified validation - makes selections optional but still validates when selections exist
    if (responsePages[currentPage]) {
        const pageConfig = responsePages[currentPage];
        const selected = document.querySelectorAll(`input[name="${pageConfig.name}"]:checked`).length;
        const maxSelections = pageConfig.type === "radio" ? 1 : getMaxSelections(pageConfig.options);

        // Only validate if at least one selection is made
        if (selected > 0 && selected > maxSelections) {
            const errorElement = document.getElementById(`${pageConfig.name}-error`);
            if (errorElement) {
                errorElement.textContent = `Please select up to ${maxSelections} options`;
                errorElement.style.display = 'block';
            }
            isValid = false;
        }
    }
    // // Page 10 validation (frustration ratings)
    // if (currentPage === 10) {
    //     // FIX: Changed validation to check for unrated items (value 0)
    //     if (frustrationRatings.some(rating => rating === 0)) {
    //         // document.getElementById('frustrations-error').style.display = 'block';
    //         isValid = false;
    //     }
    // }

    return isValid;
}

// Update selected count for a group
function updateSelectedCountForGroup(groupName) {
    const pageConfig = getPageConfigByGroupName(groupName);
    if (!pageConfig) return;

    const maxSelections = pageConfig.type === "radio" ? 1 : getMaxSelections(pageConfig.options);
    const selected = document.querySelectorAll(`input[name="${groupName}"]:checked`).length;
    const countElement = document.querySelector(`.selected-count[data-group="${groupName}"]`);

    if (countElement) {
        countElement.textContent = selected;
        countElement.style.backgroundColor = selected >= maxSelections ? "#e74c3c" : "#2f80ed";
    }

    // Disable unchecked checkboxes when max is reached
    document.querySelectorAll(`input[name="${groupName}"]`).forEach((cb) => {
        if (!cb.checked) {
            cb.disabled = selected >= maxSelections;
        }
    });
}

// Update checkbox state
function updateCheckboxState(input) {
    const option = input.closest(".radio-option, .vibe-option");
    if (option) {
        if (input.checked) {
            option.classList.add("active");
            option.setAttribute("aria-checked", "true");
        } else {
            option.classList.remove("active");
            option.setAttribute("aria-checked", "false");
        }
        // Update the icon for vibe options
        const icon = option.querySelector(".material-symbols-outlined");
        if (icon) {
            icon.textContent = input.checked ? "check" : "add";
        }

        // Add animation
        option.style.animation = "none";
        setTimeout(() => {
            option.style.animation = "bounce 0.5s ease";
        }, 10);
    }
    updateSelectedCountForGroup(input.name);
}

// Update radio state
function updateRadioState(input) {
    // Deselect all other radios in the same group
    document.querySelectorAll(`input[name="${input.name}"]`).forEach(radio => {
        const option = radio.closest('.radio-option');
        if (option) {
            option.classList.remove('active');
            option.setAttribute('aria-checked', 'false');
        }
    });

    // Select the clicked radio
    const option = input.closest(".radio-option");
    if (option) {
        option.classList.add("active");
        option.setAttribute("aria-checked", "true");

        // Add animation
        option.style.animation = "none";
        setTimeout(() => {
            option.style.animation = "bounce 0.5s ease";
        }, 10);
    }
}

// Save form data
function saveFormData() {
    // Save personal info on page 4
    if (currentPage === 4) {
        formData.personalInfo = {
            name: document.getElementById("fullName").value.trim(),
            gender: document.getElementById("gender").value,
            age: document.getElementById("age").value,
            city: document.getElementById("city").value,
            email: document.getElementById("email").value.trim(),
            phone: document.getElementById("phone").value.trim(),
            occupation: document.getElementById("occupation").value,
        };
    }

    // Save responses for question pages
    if (responsePages[currentPage]) {
        const pageConfig = responsePages[currentPage];
        const selected = document.querySelectorAll(`input[name="${pageConfig.name}"]:checked`);

        formData.responses[pageConfig.name] = {
            question: pageConfig.title,
            answers: Array.from(selected).map((input) => ({
                value: input.value,
                text: input.getAttribute("data-label") || input.value,
            })),
        };
    }

    // Save frustration ratings on page 10
    if (currentPage === 10) {
        formData.responses.frustrations = {
            question: "Rate your frustration with these struggles",
            ratings: frustrationTitles.map((title, index) => ({
                title: title,
                value: frustrationRatings[index]
            }))
        };
    }
}

// Save all responses
function saveAllResponses() {
    for (const pageNum in responsePages) {
        const pageConfig = responsePages[pageNum];
        const selected = document.querySelectorAll(`input[name="${pageConfig.name}"]:checked`);

        formData.responses[pageConfig.name] = {
            question: pageConfig.title,
            answers: Array.from(selected).map((input) => ({
                value: input.value,
                text: input.getAttribute("data-label") || input.value,
            })),
        };
    }

    // Add frustration ratings to form data
    formData.responses.frustrations = {
        question: "Rate your frustration with these struggles",
        ratings: frustrationTitles.map((title, index) => ({
            title: title,
            value: frustrationRatings[index]
        }))
    };
}

// Form submission handler
document.getElementById("submit-btn").addEventListener("click", async function () {
    if (validateCurrentPage()) {
        saveFormData();
        saveAllResponses();

        console.log("Submitting data:", JSON.stringify(formData, null, 2));

        const submitBtn = this;
        submitBtn.textContent = "Submitting...";
        submitBtn.disabled = true;
        submitBtn.classList.add("submitting");

        try {
            const response = await fetch('http://localhost:5501/submit', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    personalInfo: formData.personalInfo,
                    responses: {
                        ...formData.responses,
                        frustrations: {
                            ratings: frustrationTitles.map((title, index) => ({
                                title: title,
                                value: frustrationRatings[index]
                            }))
                        }
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                alert("Form submitted successfully!");
                resetForm();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert("Submission failed: " + error.message);
        } finally {
            submitBtn.textContent = "Submit";
            submitBtn.disabled = false;
            submitBtn.classList.remove("submitting");
        }
    }
});


// Function to reset the form
function resetForm() {
    // Reset form fields
    document.querySelectorAll("input, select").forEach((el) => {
        if (el.type !== "button" && el.type !== "submit") {
            el.value = "";
        }
    });

    // Reset checkboxes and radios
    document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach((cb) => {
        cb.checked = false;
        cb.disabled = false;
        const option = cb.closest(".radio-option, .vibe-option");
        if (option) {
            option.classList.remove("active");
            const icon = option.querySelector(".material-symbols-outlined");
            if (icon) icon.textContent = "add";
        }
    });

    // Reset selected counts
    document.querySelectorAll(".selected-count").forEach((el) => {
        el.textContent = "0";
        el.style.backgroundColor = "#2f80ed";
    });

    // Reset form data object
    formData.personalInfo = {};
    formData.responses = {};

    // Reset frustration ratings
    frustrationRatings = Array(6).fill(0);
    renderStarRatings();

    // Go to first page
    document.getElementById(`page${currentPage}`).classList.remove("active");
    document.getElementById("page1").classList.add("active");
    currentPage = 1;
    updateProgress();

    // Reset submit button
    const submitBtn = document.getElementById("submit-btn");
    submitBtn.textContent = "Submit";
    submitBtn.classList.remove("submitting");
    submitBtn.disabled = false;
}

// STAR RATING FUNCTIONS
// Function to set up star ratings
function setupStarRating(containerId) {
    const stars = document.querySelectorAll(`#${containerId} .star`);
    stars.forEach(star => {
        star.addEventListener('click', function () {
            const value = parseInt(this.getAttribute('data-value'));
            setRating(containerId, value);
        });
    });
}

// Function to set rating (with toggle functionality)
function setRating(containerId, rating) {
    const index = parseInt(containerId.split('-')[1]) - 1;
    const currentRating = frustrationRatings[index];

    // Toggle rating: if clicking the same star again, reset to 0
    if (currentRating === rating) {
        frustrationRatings[index] = 0;
    } else {
        frustrationRatings[index] = rating;
    }

    updateStarsDisplay(containerId, frustrationRatings[index]);
    const ratingValueElement = document.getElementById(`rating-value-${index + 1}`);
    if (frustrationRatings[index] > 0) {
        ratingValueElement.textContent = `${frustrationRatings[index]} star${frustrationRatings[index] !== 1 ? 's' : ''}`;
    } else {
        ratingValueElement.textContent = "0 rated";
    }
}

// Function to update stars display
function updateStarsDisplay(containerId, rating) {
    const stars = document.querySelectorAll(`#${containerId} .star`);
    stars.forEach((star, idx) => {
        star.classList.remove('filled', 'unfilled');
        if (idx < rating) {
            star.textContent = '★';
            star.classList.add('filled');
        } else {
            star.textContent = '☆';
            star.classList.add('unfilled');
        }

        // Update hover state indicator
        star.setAttribute('data-value', idx + 1);
    });
}

// Function to render all star ratings
function renderStarRatings() {
    for (let i = 1; i <= 6; i++) {
        const containerId = `rating-${i}`;
        const rating = frustrationRatings[i - 1];
        updateStarsDisplay(containerId, rating);
        const ratingValueElement = document.getElementById(`rating-value-${i}`);
        if (rating > 0) {
            ratingValueElement.textContent = `${rating} star${rating !== 1 ? 's' : ''}`;
        } else {
            ratingValueElement.textContent = "0 rated";
        }
    }
}

// Initialize when page loads
window.onload = function () {
    updateProgress();

    // Initialize all selection counts
    Object.values(responsePages).forEach(page => {
        updateSelectedCountForGroup(page.name);
    });

    // Set up frustration ratings
    for (let i = 1; i <= 6; i++) {
        setupStarRating(`rating-${i}`);
    }
    renderStarRatings();
};