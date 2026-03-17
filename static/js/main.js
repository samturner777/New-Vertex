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

if (reportForm) {
  reportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    reportNote.textContent = "Submitting...";
    const formData = new FormData(reportForm);
    const res = await fetch("/subscribe-report", { method: "POST", body: formData });
    const data = await res.json();
    if (data.download) {
      window.location.href = data.download;
      return;
    }
    reportNote.textContent = data.message || "Thank you. Please check your inbox.";
  });
}

if (newsletterForm) {
  newsletterForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(newsletterForm);
    const res = await fetch("/newsletter/subscribe", { method: "POST", body: formData });
    const data = await res.json();
    if (newsletterNote) {
      newsletterNote.textContent = data.message || "Thank you for subscribing.";
    }
    if (data.ok) {
      newsletterForm.reset();
    }
  });
}

if (contactForm) {
  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(contactForm);
    const res = await fetch("/contact/submit", { method: "POST", body: formData });
    const data = await res.json();
    if (contactNote) {
      contactNote.textContent = data.message || "Thank you for reaching out.";
    }
    if (data.ok) {
      contactForm.reset();
    }
  });
}
