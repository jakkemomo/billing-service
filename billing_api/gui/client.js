// A reference to Stripe.js initialized with your real test publishable API key.
var stripe = Stripe(
  "pk_test_51Imm7vKDxYta8liOynguNa9HGvYmSD68Oy0gPmNGBC2LPHLCC0UUHnJcF18dM45BQGrz5xfVuJfFyRDWnVSf0Xv000uXio38E1"
);

// The items the customer wants to buy
var purchase = {
  "product_id": "283f179c-5cac-43fc-a246-8f6670a26b4d",
  "email": "example@admin.com",
  "payment_system": "stripe"
};

// Disable the button until we have Stripe set up on the page
document.querySelector("button").disabled = true;
fetch("/api/user/payment", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJtb3ZpZXMtYXV0aC1zZXJ2aWNlIiwiYXVkIjoibW92aWVzLWF1dGgtc2VydmljZSIsImV4cCI6MTYyMjA0MDY1My40OTIxMTUsImlhdCI6MTYyMjAzODg1My40OTIxMTUsInNpZCI6IjdhNjA3NjlmLWM4ZTctNDYyZi05M2JlLWMwMmE4MGU4MjRhNSIsInN1YiI6IjNmYzFlMTFhLWQ3YTEtNDIzMS1hY2EwLTMxNTk4YmY1ZTA4NCIsInJscyI6e319.UxUzwrH5E8n2uzrc2ra7g1yMpBlqp47k0VZeW8g1WYRp4idTcRSzh98IxZ8jmNgY4bsVBTlEQoX1glJnlJev15gsLcv6Q-JNpoLJjUgrzZ4e_J44xB6fBQE3qQEgbd7Heupkk-IP6-LBoR64wn2_aG4KNjwqozWU5_oGPsUgueP1FIclDJULXh9hi-kAB8ODC6INEbRbWQRuNDokr7g__DwXzHcaihRz8xBBx2IZ-TW6Fk6UFnPDoPAepkaPqGrSbIFqHBxol88uBeN_QLmFl22E-FHMn60uKOyQ90c9lX8okt2k5pMiVnx7XtsDo6iGJ-q0ecLmnk3ZV8JmtNsQKg"
  },
  body: JSON.stringify(purchase),
})
  .then(function (result) {
    return result.json();
  })
  .then(function (data) {
    var elements = stripe.elements();

    var style = {
      base: {
        color: "#32325d",
        fontFamily: "Arial, sans-serif",
        fontSmoothing: "antialiased",
        fontSize: "16px",
        "::placeholder": {
          color: "#32325d",
        },
      },
      invalid: {
        fontFamily: "Arial, sans-serif",
        color: "#fa755a",
        iconColor: "#fa755a",
      },
    };

    var card = elements.create("card", { style: style });
    // Stripe injects an iframe into the DOM
    card.mount("#card-element");

    card.on("change", function (event) {
      // Disable the Pay button if there are no card details in the Element
      document.querySelector("button").disabled = event.empty;
      document.querySelector("#card-error").textContent = event.error
        ? event.error.message
        : "";
    });

    var form = document.getElementById("payment-form");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      // Complete payment when the submit button is clicked
      payWithCard(stripe, card, data.client_secret);
    });
  });

// Calls stripe.confirmCardPayment
// If the card requires authentication Stripe shows a pop-up modal to
// prompt the user to enter authentication details without leaving your page.
var payWithCard = function (stripe, card, clientSecret) {
  loading(true);
  stripe
    .confirmCardPayment(clientSecret, {
      payment_method: {
        card: card,
      },
    })
    .then(function (result) {
      if (result.error) {
        // Show error to your customer
        showError(result.error.message);
      } else {
        // The payment succeeded!
        orderComplete(result.paymentIntent.id);
      }
    });
};

/* ------- UI helpers ------- */

// Shows a success message when the payment is complete
var orderComplete = function (paymentIntentId) {
  loading(false);
  // document
  //   .querySelector(".result-message a")
  //   .setAttribute(
  //     "href",
  //     "https://dashboard.stripe.com/test/payments/" + paymentIntentId
  //   );
  document.querySelector(".result-message").classList.remove("hidden");
  document.querySelector("button").disabled = true;
};

// Show the customer the error from Stripe if their card fails to charge
var showError = function (errorMsgText) {
  loading(false);
  var errorMsg = document.querySelector("#card-error");
  errorMsg.textContent = errorMsgText;
  setTimeout(function () {
    errorMsg.textContent = "";
  }, 4000);
};

// Show a spinner on payment submission
var loading = function (isLoading) {
  if (isLoading) {
    // Disable the button and show a spinner
    document.querySelector("button").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("button").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
};
