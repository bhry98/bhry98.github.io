/* Share buttons for blog posts: copy link + native share sheet (mobile). */
(function () {
  function showNativeButtons() {
    if (!navigator.share) return;
    document.querySelectorAll(".bh-share__btn--native").forEach(function (btn) {
      btn.hidden = false;
    });
  }

  document.addEventListener("click", function (event) {
    var copyBtn = event.target.closest("[data-bh-copy]");
    if (copyBtn) {
      var url = copyBtn.getAttribute("data-bh-copy");
      var label = copyBtn.querySelector("span");
      var done = function () {
        label.textContent = "Copied!";
        copyBtn.classList.add("is-done");
        setTimeout(function () {
          label.textContent = "Copy link";
          copyBtn.classList.remove("is-done");
        }, 2000);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link:", url); });
      } else {
        window.prompt("Copy this link:", url);
      }
      return;
    }

    var shareBtn = event.target.closest("[data-bh-share-url]");
    if (shareBtn && navigator.share) {
      navigator.share({
        title: shareBtn.getAttribute("data-bh-share-title"),
        url: shareBtn.getAttribute("data-bh-share-url")
      }).catch(function () {});
    }
  });

  // Material's instant navigation swaps pages without a reload.
  if (window.document$) {
    window.document$.subscribe(showNativeButtons);
  } else {
    document.addEventListener("DOMContentLoaded", showNativeButtons);
  }
})();
