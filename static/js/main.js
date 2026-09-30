const modal = document.getElementById("report-modal");
const reportForm = document.getElementById("report-form");
const reportId = document.getElementById("report-id");
const reportNote = document.getElementById("report-note");
const newsletterForm = document.getElementById("newsletter-form");
const newsletterNote = document.getElementById("newsletter-note");
const contactForm = document.getElementById("contact-form");
const contactNote = document.getElementById("contact-note");

if (modal) {
  document.querySelectorAll("[data-report]").forEach((btn) => {
    btn.addEventListener("click", () => {
      reportId.value = btn.dataset.report;
      reportNote.textContent = "";
      modal.classList.add("active");
      modal.setAttribute("aria-hidden", "false");
    });
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.classList.contains("modal-close")) {
      modal.classList.remove("active");
      modal.setAttribute("aria-hidden", "true");
    }
  });
}

async function submitForm(form, endpoint, note, successMessage) {
  const response = await fetch(endpoint, {
    method: "POST",
    body: new FormData(form),
  });
  const data = await response.json();
  note.textContent = data.message || successMessage;
  if (data.ok) {
    form.reset();
  }
  return data;
}

if (reportForm) {
  reportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    reportNote.textContent = "Submitting...";
    const data = await submitForm(
      reportForm,
      "/subscribe-report",
      reportNote,
      "Thank you. Please check your inbox."
    );
    if (data.download) {
      window.location.href = data.download;
    }
  });
}

if (newsletterForm && newsletterNote) {
  newsletterForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitForm(
      newsletterForm,
      "/newsletter/subscribe",
      newsletterNote,
      "Thank you for subscribing."
    );
  });
}

if (contactForm && contactNote) {
  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitForm(
      contactForm,
      "/contact/submit",
      contactNote,
      "Thank you for reaching out."
    );
  });
}

let currentAudio = null;

function toggleAudio(button) {
  const audioPlayer = button.closest(".report-card")?.querySelector(".report-audio-player");
  const audio = audioPlayer?.querySelector("audio") || audioPlayer;
  if (!audio) {
    return;
  }

  if (currentAudio && currentAudio !== audio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    document.querySelectorAll(".play-button").forEach((btn) => {
      btn.classList.remove("playing");
    });
  }

  if (audio.paused) {
    audio.play();
    button.classList.add('playing');
    currentAudio = audio;
  } else {
    audio.pause();
    audio.currentTime = 0;
    button.classList.remove('playing');
    currentAudio = null;
  }

  audio.onended = () => {
    button.classList.remove('playing');
    currentAudio = null;
  };
}