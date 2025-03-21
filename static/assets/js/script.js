var ctx1 = document.getElementById("chart-line").getContext("2d");

var gradientStroke1 = ctx1.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgba(94, 114, 228, 0.2)");
gradientStroke1.addColorStop(0.2, "rgba(94, 114, 228, 0.0)");
gradientStroke1.addColorStop(0, "rgba(94, 114, 228, 0)");
new Chart(ctx1, {
  type: "line",
  data: {
    labels: ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    datasets: [
      {
        label: "Mobile apps",
        tension: 0.4,
        borderWidth: 0,
        pointRadius: 0,
        borderColor: "#5e72e4",
        backgroundColor: gradientStroke1,
        borderWidth: 3,
        fill: true,
        data: [50, 40, 300, 220, 500, 250, 400, 230, 500],
        maxBarThickness: 6,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    interaction: {
      intersect: false,
      mode: "index",
    },
    scales: {
      y: {
        grid: {
          drawBorder: false,
          display: true,
          drawOnChartArea: true,
          drawTicks: false,
          borderDash: [5, 5],
        },
        ticks: {
          display: true,
          padding: 10,
          color: "#fbfbfb",
          font: {
            size: 11,
            family: "Open Sans",
            style: "normal",
            lineHeight: 2,
          },
        },
      },
      x: {
        grid: {
          drawBorder: false,
          display: false,
          drawOnChartArea: false,
          drawTicks: false,
          borderDash: [5, 5],
        },
        ticks: {
          display: true,
          color: "#ccc",
          padding: 20,
          font: {
            size: 11,
            family: "Open Sans",
            style: "normal",
            lineHeight: 2,
          },
        },
      },
    },
  },
});

function toggleCart() {
  const cartPopup = document.getElementById("cart-popup");
  cartPopup.style.display =
    cartPopup.style.display === "none" ? "flex" : "none";
  fetchCartItems(); // Fetch items when cart is toggled
}

// Fetch cart items from the server
async function fetchCartItems() {
  try {
    const response = await fetch("/calculate/");
    if (response.ok) {
      const cartData = await response.json();
      displayCartItems(cartData); // Pass the data to display function
    } else {
      console.error("Failed to fetch cart items");
    }
  } catch (error) {
    console.error("Error fetching cart items:", error);
  }
}

// Display cart items
function displayCartItems(cartData) {
  const cartBox = document.getElementById("cart-box");
  cartBox.innerHTML = ""; // Clear the existing cart items
  cartData.forEach((item) => {
    const itemElement = document.createElement("div");
    itemElement.classList.add("cart-item");

    itemElement.innerHTML = `
              <img src="${item.image_url}" alt="${item.name}" width="50" height="50" />
              <div class="cart-item-name">${item.name}</div>
              <div class="cart-item-qty">
                  <button onclick="changeQuantity('${item.name}', -1)">-</button>
                  <span>${item.quantity}</span>
                  <button onclick="changeQuantity('${item.name}', 1)">+</button>
              </div>
          `;
    cartBox.appendChild(itemElement);
  });
}

// Change quantity of cart item
function changeQuantity(itemName, change) {
  const itemElement = Array.from(
    document.getElementsByClassName("cart-item")
  ).find((el) => el.querySelector(".cart-item-name").textContent === itemName);
  const quantityElement = itemElement.querySelector(".cart-item-qty span");
  let currentQuantity = parseInt(quantityElement.textContent);
  currentQuantity += change;
  if (currentQuantity < 1) currentQuantity = 1; // Prevent negative or zero quantity
  quantityElement.textContent = currentQuantity;
}
var win = navigator.platform.indexOf("Win") > -1;
if (win && document.querySelector("#sidenav-scrollbar")) {
  var options = {
    damping: "0.5",
  };
  Scrollbar.init(document.querySelector("#sidenav-scrollbar"), options);
}

// dashboard js
document.addEventListener("DOMContentLoaded", function () {
  const data = {
    labels: ["Fruits", "Vegetables", "Dairy", "Bakery", "Meat & Fish"], // Food categories
    datasets: [
      {
        label: "Wasted Food (kg)",
        data: [200, 150, 80, 70, 60], // Static data values for each category
        backgroundColor: [
          "#172b4d",
          "#11cdef",
          "#f5365c",
          "#2dce89",
          "#fb6340",
        ],
        borderColor: "#333",
        borderWidth: 1,
      },
    ],
  };

  const config = {
    type: "bar",
    data: data,
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Wastage (kg)",
          },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.raw + " kg"; // Show data in kg
            },
          },
        },
      },
    },
  };

  const ctx = document.getElementById("bar-chart").getContext("2d");
  new Chart(ctx, config);
});

//  JavaScript for static data pie chart
document.addEventListener("DOMContentLoaded", function () {
  const data = {
    labels: ["Fruits", "Vegetables", "Dairy", "Bakery", "Meat & Fish"],
    datasets: [
      {
        label: "Top Wasted Food Categories",
        data: [30, 20, 15, 18, 17], // Static data values (e.g., percentages or waste amounts)
        backgroundColor: [
          "#ff6384",
          "#36a2eb",
          "#ffce56",
          "#4bc0c0",
          "#9966ff",
        ],
        hoverOffset: 4,
      },
    ],
  };

  const config = {
    type: "pie",
    data: data,
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.label || "";
              if (label) {
                label += ": ";
              }
              label += context.raw + "%"; // Show as percentage
              return label;
            },
          },
        },
      },
    },
  };

  const ctx = document.getElementById("pie-chart").getContext("2d");
  new Chart(ctx, config);
});
