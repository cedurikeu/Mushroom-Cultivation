document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 JavaScript is running!");

  const groupBuilding = document.querySelector(".group-building");
  const circles = document.querySelectorAll(".circle");

  // Initially hide circles
  circles.forEach((circle) => {
    circle.style.opacity = "0";
    circle.style.transform = "scale(0.8)";
    circle.style.transition =
      "opacity 0.5s ease-in-out, transform 0.3s ease-in-out"; // Shortened transition for scaling

    // Ensure circles are clickable
    circle.style.pointerEvents = "auto";
    circle.style.cursor = "pointer";
  });

  // Toggle circle visibility when clicking the building
  groupBuilding.addEventListener("click", () => {
    circles.forEach((circle) => {
      const isVisible = circle.style.opacity === "1";
      circle.style.opacity = isVisible ? "0" : "1";
      circle.style.transform = isVisible ? "scale(0.8)" : "scale(1)";
    });
  });

  // Add event listeners to each circle for clicking and hovering
  circles.forEach((circle) => {
    // Hover effect for scaling
    circle.addEventListener("mouseenter", () => {
      circle.style.transform = "scale(1.05)"; // Slightly increase size on hover
    });

    circle.addEventListener("mouseleave", () => {
      circle.style.transform = "scale(1)"; // Return to normal size when not hovering
    });

    // Click effect to scale up further
    circle.addEventListener("click", (event) => {
      event.stopPropagation();
      circle.style.backgroundColor = "hsla(0, 0%, 91%, 0.918)";
      setTimeout(() => {
        circle.style.backgroundColor = "#d9d9d9";
      }, 300); // Scale back to normal size after 2 seconds
    });
  });
});
