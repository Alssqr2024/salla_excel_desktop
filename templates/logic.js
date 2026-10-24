<script>
  let parsedProducts = [];
  let currentResults = [];
  let currentPreviewContext = null;

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط±ظپط¹ ط§ظ„ظ…ظ„ظپ
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  async function uploadFile() {
    const fileInput = document.getElementById("excel-file");
    const btn = document.getElementById("upload-btn");

    if (!fileInput.files.length) {
      alert("ط§ط®طھط± ظ…ظ„ظپظ‹ط§ ط£ظˆظ„ظ‹ط§");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    btn.disabled = true;
    btn.innerHTML =
      '<span class="loading loading-spinner loading-sm"></span> ط¬ط§ط±ظچ ط§ظ„طھط­ظ„ظٹظ„...';

    try {
      const res = await fetch("/api/parse", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ظپط´ظ„ ط§ظ„طھط­ظ„ظٹظ„");

      parsedProducts = data.products;
      renderPreview(data);
      document.getElementById("preview-panel").classList.remove("hidden");
      document.getElementById("upload-panel").classList.add("hidden");
      document.getElementById("sticky-toolbar").classList.remove("hidden");
      document.getElementById("toolbar-products-count").textContent =
        `${data.total} ظ…ظ†طھط¬`;
    } catch (e) {
      alert("â‌Œ " + e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = "ًں“¤ ط±ظپط¹ ظˆطھط­ظ„ظٹظ„ ط§ظ„ظ…ظ„ظپ";
    }
  }

  function renderPreview(data) {
    document.getElementById("products-count").textContent =
      `${data.total} ظ…ظ†طھط¬`;

    const detected = Object.entries(data.columns_detected)
      .map(([k, v]) => `${k}â†’${v}`)
      .join(" | ");
    document.getElementById("columns-detected").textContent =
      `ًں”چ ط§ظ„ط£ط¹ظ…ط¯ط© ط§ظ„ظ…ظƒطھط´ظپط©: ${detected}`;

    const tbody = document.getElementById("preview-tbody");
    tbody.innerHTML = data.products
      .slice(0, 100)
      .map(
        (p, i) => `
        <tr>
            <td>${i + 1}</td>
            <td class="font-semibold">${escapeHtml(p.name)}</td>
            <td class="font-mono text-xs">${escapeHtml(p.barcode || "â€”")}</td>
            <td>${escapeHtml(p.price || "â€”")}</td>
            <td>${escapeHtml(p.quantity || "â€”")}</td>
        </tr>
    `,
      )
      .join("");
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„طµظˆط± - طھظ„ظ‚ط§ط¦ظٹ ط¨ط§ظ„ظƒط§ظ…ظ„ ط®ظ„ظپ ط§ظ„ظƒظˆط§ظ„ظٹط³
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  async function startImageSearch() {
    const btns = [
      document.getElementById("search-btn"),
      document.getElementById("search-btn-2"),
    ].filter(Boolean);

    btns.forEach((b) => {
      b.disabled = true;
      b.innerHTML =
        '<span class="loading loading-spinner loading-sm"></span> ط¬ط§ط±ظچ...';
    });

    document.getElementById("preview-panel").classList.add("hidden");
    document.getElementById("progress-panel").classList.remove("hidden");
    document.getElementById("results-panel").classList.add("hidden");

    // ط¥ط¹ط§ط¯ط© طھط¹ظٹظٹظ† ط´ط±ظٹط· ط§ظ„طھظ‚ط¯ظ…
    document.getElementById("progress-circle").style.setProperty("--value", 0);
    document.getElementById("progress-circle").textContent = "0%";
    document.getElementById("progress-bar").value = 0;
    document.getElementById("progress-count").textContent =
      `0 / ${parsedProducts.length}`;
    document.getElementById("progress-status").textContent =
      "âڈ³ طھط¬ظ‡ظٹط² ظ…ط­ط±ظƒ ط§ظ„ط¨ط­ط«...";
    document.getElementById("progress-detail").textContent =
      "ط³ظٹط¨ط¯ط£ طھظ„ظ‚ط§ط¦ظٹظ‹ط§...";

    const jobId =
      "job_" + Date.now() + "_" + Math.random().toString(36).substring(2, 8);

    // ظ…طھط§ط¨ط¹ط© ط§ظ„طھظ‚ط¯ظ…
    let pollInterval = setInterval(async () => {
      try {
        const r = await fetch(`/api/progress/${jobId}`);
        const p = await r.json();
        const percent =
          p.total > 0 ? Math.round((p.processed / p.total) * 100) : 0;

        document
          .getElementById("progress-circle")
          .style.setProperty("--value", percent);
        document.getElementById("progress-circle").textContent = percent + "%";
        document.getElementById("progress-bar").value = percent;
        document.getElementById("progress-count").textContent =
          `${p.processed} / ${p.total} (ظ†ط¬ط­: ${p.succeeded} | ظپط´ظ„: ${p.failed})`;

        if (p.status === "preparing") {
          document.getElementById("progress-status").textContent =
            "ًں”§ طھط¬ظ‡ظٹط² ظ…ط­ط±ظƒ ط§ظ„ط¨ط­ط«...";
          document.getElementById("progress-detail").textContent =
            p.current || "ظٹط±ط¬ظ‰ ط§ظ„ط§ظ†طھط¸ط§ط±";
        } else if (p.status === "processing") {
          document.getElementById("progress-status").textContent =
            "ًں”چ ط§ظ„ط¨ط­ط« ط¹ظ† طµظˆط±...";
          document.getElementById("progress-detail").textContent = p.current
            ? `ًں”چ ${p.current}`
            : "";
        } else if (p.status === "completed") {
          document.getElementById("progress-status").textContent =
            "âœ… ط§ظƒطھظ…ظ„ ط§ظ„ط¨ط­ط«";
          clearInterval(pollInterval);
        } else if (p.status === "failed") {
          document.getElementById("progress-status").textContent =
            "â‌Œ ظپط´ظ„ ط§ظ„ط¨ط­ط«";
          clearInterval(pollInterval);
        }
      } catch (e) {}
    }, 1000);

    const useAi = document.getElementById("use-ai")?.checked ?? true;

    try {
      const res = await fetch("/api/search-images", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          products: parsedProducts,
          use_ai: useAi,
          job_id: jobId,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ظپط´ظ„ ط§ظ„ط¨ط­ط«");

      clearInterval(pollInterval);

      document
        .getElementById("progress-circle")
        .style.setProperty("--value", 100);
      document.getElementById("progress-circle").textContent = "100%";
      document.getElementById("progress-bar").value = 100;
      document.getElementById("progress-status").textContent = "âœ… ط§ظƒطھظ…ظ„ ط§ظ„ط¨ط­ط«";
      document.getElementById("progress-detail").textContent =
        `ظ†ط¬ط­: ${data.summary.success} | ظپط´ظ„: ${data.summary.failed} | ط§ظ„ظˆظ‚طھ: ${data.summary.elapsed}s`;

      currentResults = data.results;

      setTimeout(() => {
        document.getElementById("progress-panel").classList.add("hidden");
        document.getElementById("results-panel").classList.remove("hidden");
        renderResults(data.results);
      }, 800);
    } catch (e) {
      clearInterval(pollInterval);
      alert("â‌Œ " + e.message);
    } finally {
      btns.forEach((b) => {
        b.disabled = false;
        if (b.id === "search-btn") b.innerHTML = "ًں”چ ط§ظ„ط¨ط­ط« ط¹ظ† طµظˆط± ظ„ظƒظ„ ط§ظ„ظ…ظ†طھط¬ط§طھ";
        else b.innerHTML = "ًں”چ ط§ظ„ط¨ط­ط« ط¹ظ† ط§ظ„طµظˆط±";
      });
    }
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط¹ط±ط¶ ط§ظ„ظ†طھط§ط¦ط¬
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function scoreColor(score) {
    if (score >= 80) return "badge-success";
    if (score >= 60) return "badge-warning";
    return "badge-error";
  }

  function renderResults(results) {
    currentResults = results;
    const tbody = document.getElementById("results-tbody");
    const successCount = results.filter((r) => r.search_success).length;

    // ط­ظپط¸ ط§ظ„طھط­ط¯ظٹط¯ط§طھ ط§ظ„ط³ط§ط¨ظ‚ط© ط¥ظ† ظˆظڈط¬ط¯طھ
    const previousSelected = new Set();
    const existingCheckboxes = document.querySelectorAll(".result-checkbox");
    const hadExistingCheckboxes = existingCheckboxes.length > 0;
    existingCheckboxes.forEach((cb) => {
      if (cb.checked) {
        previousSelected.add(parseInt(cb.dataset.index));
      }
    });

    document.getElementById("results-summary-info").innerHTML = `
        <div class="alert alert-info py-2">
            <span>ًں“ٹ ظ†ط¬ط­: <strong>${successCount}</strong> / ${results.length} |
                  â‌Œ ظپط´ظ„: <strong>${results.length - successCount}</strong></span>
        </div>
    `;

    tbody.innerHTML = results
      .map((r, i) => {
        const displayUrl = r.image_url || r.candidates?.[0]?.image_url || null;
        const isChecked = hadExistingCheckboxes ? previousSelected.has(i) : !!displayUrl;

        const mainImage = displayUrl
          ? `<img src="${escapeAttr(displayUrl)}"
                    class="w-20 h-20 object-cover rounded-lg cursor-pointer
                           hover:ring-2 hover:ring-primary transition-all shadow"
                    onclick="openPreviewModal(${i}, -1)"
                    onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2280%22>ًں–¼ï¸ڈ</text></svg>'">`
          : `<div class="w-20 h-20 bg-base-300 rounded-lg flex items-center justify-center text-2xl">â‌Œ</div>`;

        const candidates = r.candidates || [];
        const alternativesHtml =
          candidates.length > 1
            ? candidates
                .slice(1, 5)
                .map(
                  (c, cIdx) => `
                <img src="${escapeAttr(c.image_url)}"
                     class="w-12 h-12 object-cover rounded cursor-pointer
                            hover:ring-2 hover:ring-info transition-all"
                     title="${escapeAttr(c.title || '')} - ط¯ط±ط¬ط©: ${c.score || ''}"
                     onclick="openPreviewModal(${i}, ${cIdx + 1})">
            `,
                )
                .join("")
            : '<span class="text-xs text-base-content/60">â€”</span>';

        const aiUsed = r.ai_vision && r.ai_vision.used;
        const aiBadge = aiUsed
          ? `<span class="badge badge-xs badge-info" title="${escapeAttr(r.ai_vision?.reasoning || "")}">ًں¤–</span>`
          : "";
        const smartBadge = r.smart_search_used
          ? `<span class="badge badge-xs badge-warning">ًں§ </span>`
          : "";
        const manualBadge = r.manual_selection
          ? `<span class="badge badge-xs badge-success">â­گ</span>`
          : "";

        const scoreBadge = r.search_score
          ? `<div class="flex gap-1 items-center flex-wrap">
                   ${aiBadge}${smartBadge}${manualBadge}
                   <span class="badge badge-sm ${scoreColor(r.search_score)}">${r.search_score}</span>
               </div>`
          : '<span class="badge badge-sm badge-error">â€”</span>';

        return `
            <tr id="result-row-${i}" data-index="${i}">
                <td>
                    <input type="checkbox" class="result-checkbox checkbox checkbox-sm checkbox-primary"
                           data-index="${i}" onchange="updateSelectionCount()" ${isChecked ? 'checked' : ''}>
                </td>
                <td>${mainImage}</td>
                <td>
                    <div class="font-semibold">${escapeHtml(r.name)}</div>
                    ${
                      r.search_success
                        ? '<span class="text-xs text-success">âœ… ظˆط¬ط¯طھ طµظˆط±ط©</span>'
                        : `<span class="text-xs text-warning">âڑ ï¸ڈ ${escapeHtml(r.error || "طھط­ظ‚ظ‚ ظٹط¯ظˆظٹظ‹ط§")}</span>`
                    }
                </td>
                <td class="font-mono text-xs">${escapeHtml(r.barcode || "â€”")}</td>
                <td>${escapeHtml(r.price || "â€”")}</td>
                <td>${scoreBadge}</td>
                <td><div class="flex gap-1 flex-wrap">${alternativesHtml}</div></td>
            </tr>
        `;
      })
      .join("");

    updateSelectionCount();
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // طھط­ط¯ظٹط¯ ط§ظ„ظپط§ط´ظ„ط© ظپظ‚ط·
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function selectOnlyFailed() {
    let count = 0;
    document.querySelectorAll(".result-checkbox").forEach((cb) => {
      const idx = parseInt(cb.dataset.index);
      const r = currentResults[idx];
      const isFailed =
        !r.search_success ||
        !r.image_url ||
        r.decision === "manual_review" ||
        r.decision === "ai_rejected_all";
      cb.checked = isFailed;
      if (isFailed) count++;
    });
    updateSelectionCount();
    alert(
      count > 0
        ? `âœ… طھظ… طھط­ط¯ظٹط¯ ${count} ظ…ظ†طھط¬ظ‹ط§ ظپط§ط´ظ„ظ‹ط§`
        : "âœ… ظ„ط§ طھظˆط¬ط¯ ظ…ظ†طھط¬ط§طھ ظپط§ط´ظ„ط©",
    );
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ظ…ط¹ط§ظٹظ†ط© ط§ظ„طµظˆط±ط©
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function openPreviewModal(productIndex, candidateIndex = -1) {
    const product = currentResults[productIndex];
    if (!product) return;

    let targetUrl = "";
    let targetTitle = "";

    if (candidateIndex === -1) {
      targetUrl = product.image_url || product.candidates?.[0]?.image_url || "";
      targetTitle = product.top_title || product.candidates?.[0]?.title || "ط§ظ„طµظˆط±ط© ط§ظ„ط£ط³ط§ط³ظٹط© ط§ظ„ط­ط§ظ„ظٹط©";
    } else {
      const cand = product.candidates?.[candidateIndex];
      if (cand) {
        targetUrl = cand.image_url;
        targetTitle = `${cand.title || "طµظˆط±ط© ط¨ط¯ظٹظ„ط©"} - ط¯ط±ط¬ط©: ${cand.score || ""}`;
      }
    }

    if (!targetUrl) return;

    currentPreviewContext = {
      productIndex,
      candidateIndex,
      imageUrl: targetUrl,
    };

    document.getElementById("preview-image").src = targetUrl;
    document.getElementById("preview-title").textContent = product.name;
    document.getElementById("preview-info").textContent = targetTitle;

    const setBtn = document.getElementById("set-as-main-btn");
    const currentBadge = document.getElementById("current-main-badge");

    const currentMain = product.image_url || product.candidates?.[0]?.image_url;
    const isCurrentMain = targetUrl === currentMain;

    if (isCurrentMain) {
      currentBadge.classList.remove("hidden");
      setBtn.classList.remove("hidden");
      setBtn.disabled = true;
      setBtn.innerHTML = "âœ… ظ‡ط°ظ‡ ظ‡ظٹ ط§ظ„طµظˆط±ط© ط§ظ„ط£ط³ط§ط³ظٹط©";
    } else {
      currentBadge.classList.add("hidden");
      setBtn.classList.remove("hidden");
      setBtn.disabled = false;
      setBtn.innerHTML = "â­گ طھط¹ظٹظٹظ† ظƒطµظˆط±ط© ط£ط³ط§ط³ظٹط©";
    }

    document.getElementById("image-preview-modal").showModal();
  }

  // ظ„ظ„طھظˆط§ظپظ‚ ظ…ط¹ ط£ظٹ ط§ط³طھط¯ط¹ط§ط،ط§طھ ظ‚ط¯ظٹظ…ط©
  function openPreview(imageUrl, productName, info, productIndex = null, isAlternative = false) {
    if (productIndex !== null && productIndex >= 0) {
      const product = currentResults[productIndex];
      if (product && product.candidates) {
        const cIdx = product.candidates.findIndex(c => c.image_url === imageUrl);
        if (cIdx >= 0) {
          openPreviewModal(productIndex, cIdx);
          return;
        }
      }
      openPreviewModal(productIndex, -1);
      return;
    }
    document.getElementById("preview-image").src = imageUrl;
    document.getElementById("preview-title").textContent = productName;
    document.getElementById("preview-info").textContent = info || "";
    document.getElementById("set-as-main-btn").classList.add("hidden");
    document.getElementById("current-main-badge").classList.add("hidden");
    document.getElementById("image-preview-modal").showModal();
  }

  function setAsMainImage() {
    if (!currentPreviewContext || currentPreviewContext.productIndex === null)
      return;
    const idx = currentPreviewContext.productIndex;
    const imageUrl = currentPreviewContext.imageUrl;
    const candidateIndex = currentPreviewContext.candidateIndex;
    const product = currentResults[idx];
    if (!product) return;

    product.image_url = imageUrl;
    product.search_success = true;
    product.search_score = 100;
    product.manual_selection = true;
    product.decision = "accepted";

    // ط¥ط¹ط§ط¯ط© طھط±طھظٹط¨ ظ‚ط§ط¦ظ…ط© ط§ظ„ط¨ط¯ط§ط¦ظ„ ظ„طھظƒظˆظ† ط§ظ„طµظˆط±ط© ط§ظ„ظ…ط®طھط§ط±ط© ظپظٹ ط£ظˆظ„ ط§ظ„ظ‚ط§ط¦ظ…ط©
    if (Array.isArray(product.candidates) && product.candidates.length > 0) {
      let chosenCand = null;
      if (candidateIndex !== undefined && candidateIndex >= 0 && product.candidates[candidateIndex]) {
        chosenCand = product.candidates.splice(candidateIndex, 1)[0];
      } else {
        const foundIdx = product.candidates.findIndex(c => c.image_url === imageUrl);
        if (foundIdx >= 0) {
          chosenCand = product.candidates.splice(foundIdx, 1)[0];
        }
      }
      if (chosenCand) {
        chosenCand.score = 100;
        product.candidates.unshift(chosenCand);
      } else {
        product.candidates.unshift({
          image_url: imageUrl,
          title: product.name,
          score: 100,
        });
      }
    } else {
      product.candidates = [{
        image_url: imageUrl,
        title: product.name,
        score: 100,
      }];
    }

    document.getElementById("image-preview-modal").close();
    renderResults(currentResults);

    // ط§ظ„طھط£ظƒط¯ ظ…ظ† ط£ظ† ط§ظ„ظ…ظ†طھط¬ ظ…ط­ط¯ط¯ ظپظٹ ظ‚ط§ط¦ظ…ط© ط§ظ„طھطµط¯ظٹط±
    const cb = document.querySelector(`.result-checkbox[data-index="${idx}"]`);
    if (cb) {
      cb.checked = true;
      updateSelectionCount();
    }

    const toast = document.createElement("div");
    toast.className = "toast toast-top toast-end z-50";
    toast.innerHTML = `<div class="alert alert-success shadow-lg"><span>âœ… طھظ… طھط¹ظٹظٹظ† ط§ظ„طµظˆط±ط© ظˆط§ط®طھظٹط§ط± ط§ظ„ظ…ظ†طھط¬</span></div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط¥ط¯ط§ط±ط© ط§ظ„طھط­ط¯ظٹط¯
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function toggleSelectAll(checked) {
    document
      .querySelectorAll(".result-checkbox")
      .forEach((cb) => (cb.checked = checked));
    updateSelectionCount();
  }

  function updateSelectionCount() {
    const selected = document.querySelectorAll(".result-checkbox:checked");
    const count = selected.length;
    const total = document.querySelectorAll(".result-checkbox").length;

    document.getElementById("selected-products-count").textContent =
      `${count} ظ…ط­ط¯ط¯`;

    const toolbarSelected = document.getElementById("toolbar-selected-count");
    if (count > 0) {
      toolbarSelected.textContent = `${count} ظ…ط­ط¯ط¯`;
      toolbarSelected.classList.remove("hidden");
    } else {
      toolbarSelected.classList.add("hidden");
    }

    // طھط­ط¯ظٹط« ظ†طµظˆطµ ط£ط²ط±ط§ط± ط§ظ„طھطµط¯ظٹط±
    const exportLabels = document.querySelectorAll(".export-btn-label");
    exportLabels.forEach((el) => {
      if (count > 0 && count < total) {
        el.innerHTML = `ًں“¥ طھطµط¯ظٹط± ط§ظ„ظ…ط­ط¯ط¯ (${count}) <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>`;
      } else if (count === total && total > 0) {
        el.innerHTML = `ًں“¥ طھطµط¯ظٹط± ط§ظ„ظƒظ„ (${total}) <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>`;
      } else {
        el.innerHTML = `ًں“¥ طھطµط¯ظٹط± ظ‚ط§ظ„ط¨ Salla <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>`;
      }
    });

    document.getElementById("upload-selected-btn").disabled = count === 0;
    document.getElementById("reanalyze-selected-btn").disabled = count === 0;

    const selectAll = document.getElementById("select-all-products");
    if (selectAll) {
      selectAll.checked = count === total && count > 0;
      selectAll.indeterminate = count > 0 && count < total;
    }
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط¥ط¹ط§ط¯ط© ط§ط®طھط¨ط§ط± ط§ظ„ظ…ط­ط¯ط¯
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  async function reanalyzeSelected() {
    const selected = Array.from(
      document.querySelectorAll(".result-checkbox:checked"),
    );
    if (selected.length === 0) return;
    if (!confirm(`ط³ظٹطھظ… ط¥ط¹ط§ط¯ط© ط§ط®طھط¨ط§ط± ${selected.length} ظ…ظ†طھط¬. ظ…طھط§ط¨ط¹ط©طں`)) return;

    const productsToReanalyze = selected.map((cb) => {
      const idx = parseInt(cb.dataset.index);
      const r = currentResults[idx];
      return {
        row: r.row,
        name: r.name,
        barcode: r.barcode,
        price: r.price,
        quantity: r.quantity,
        description: r.description,
      };
    });

    document.getElementById("progress-panel").classList.remove("hidden");
    document.getElementById("results-panel").classList.add("hidden");
    document.getElementById("progress-count").textContent =
      `0 / ${productsToReanalyze.length}`;
    document.getElementById("progress-status").textContent =
      "ًں”§ طھط¬ظ‡ظٹط² ظ…ط­ط±ظƒ ط§ظ„ط¨ط­ط«...";
    document.getElementById("progress-detail").textContent =
      "ط³ظٹط¨ط¯ط£ طھظ„ظ‚ط§ط¦ظٹظ‹ط§...";

    const useAi = document.getElementById("use-ai")?.checked ?? true;
    const jobId = "re_" + Date.now();

    let fakeProgress = 0;
    const interval = setInterval(() => {
      fakeProgress = Math.min(fakeProgress + 5, 90);
      document
        .getElementById("progress-circle")
        .style.setProperty("--value", fakeProgress);
      document.getElementById("progress-circle").textContent =
        fakeProgress + "%";
    }, 500);

    try {
      const res = await fetch("/api/search-images", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          products: productsToReanalyze,
          use_ai: useAi,
          job_id: jobId,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ظپط´ظ„ ط¥ط¹ط§ط¯ط© ط§ظ„ط§ط®طھط¨ط§ط±");

      clearInterval(interval);
      document
        .getElementById("progress-circle")
        .style.setProperty("--value", 100);
      document.getElementById("progress-circle").textContent = "100%";
      document.getElementById("progress-status").textContent =
        "âœ… ط§ظƒطھظ…ظ„طھ ط¥ط¹ط§ط¯ط© ط§ظ„ط§ط®طھط¨ط§ط±";

      selected.forEach((cb, i) => {
        const idx = parseInt(cb.dataset.index);
        currentResults[idx] = data.results[i];
      });

      setTimeout(() => {
        document.getElementById("progress-panel").classList.add("hidden");
        document.getElementById("results-panel").classList.remove("hidden");
        renderResults(currentResults);
      }, 800);
    } catch (e) {
      clearInterval(interval);
      alert("â‌Œ " + e.message);
    }
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط±ظپط¹ ط¥ظ„ظ‰ Salla
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  async function uploadSelectedToSalla() {
    const selected = Array.from(
      document.querySelectorAll(".result-checkbox:checked"),
    );
    if (selected.length === 0) return;

    const items = selected.map((cb) => {
      const idx = parseInt(cb.dataset.index);
      const r = currentResults[idx];
      return {
        name: r.name,
        barcode: r.barcode,
        sku: r.sku || r.barcode,
        price: r.price,
        quantity: r.quantity,
        description: r.description,
        image_url: r.image_url || r.candidates?.[0]?.image_url || "",
      };
    });

    if (!confirm(`ط³ظٹطھظ… ط¥ظ†ط´ط§ط،/طھط­ط¯ظٹط« ${items.length} ظ…ظ†طھط¬ ظپظٹ Salla. ظ…طھط§ط¨ط¹ط©طں`))
      return;

    document.getElementById("upload-modal").showModal();
    document.getElementById("upload-results").classList.add("hidden");
    document.getElementById("upload-close-btn").disabled = true;

    try {
      const res = await fetch(
        "/dashboard/import-excel/upload-selected-to-salla",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ items }),
        },
      );

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "ظپط´ظ„ ط§ظ„ط±ظپط¹");

      document.getElementById("upload-progress").innerHTML = `
            <div class="alert alert-info">
                <div>
                    <p class="font-bold">ًں“ٹ ط§ظ„ظ†طھظٹط¬ط©</p>
                    <p>âœ… ظ†ط¬ط­: <strong class="text-success">${data.summary.success}</strong></p>
                    <p>â‌Œ ظپط´ظ„: <strong class="text-error">${data.summary.failed}</strong></p>
                </div>
            </div>
        `;

      const resultsEl = document.getElementById("upload-results");
      resultsEl.classList.remove("hidden");
      resultsEl.innerHTML = `
            <details open>
                <summary class="cursor-pointer font-bold mb-2">ًں“‹ ط§ظ„طھظپط§طµظٹظ„</summary>
                <ul class="text-sm space-y-1 max-h-72 overflow-y-auto">
                    ${data.results
                      .map(
                        (r) => `
                        <li class="${r.success ? "text-success" : "text-error"}">
                            ${r.success ? "âœ…" : "â‌Œ"} ${escapeHtml(r.name)}
                            ${r.image_status ? ` - ${r.image_status}` : ""}
                            ${r.error ? `<br><span class="text-xs opacity-80">${escapeHtml(r.error)}</span>` : ""}
                        </li>
                    `,
                      )
                      .join("")}
                </ul>
            </details>
        `;
      document.getElementById("upload-close-btn").disabled = false;
    } catch (e) {
      document.getElementById("upload-progress").innerHTML = `
            <div class="alert alert-error"><span>â‌Œ ${escapeHtml(e.message)}</span></div>
        `;
      document.getElementById("upload-close-btn").disabled = false;
    }
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // طھطµط¯ظٹط±
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  async function exportSallaTemplate(templateType = "new") {
    if (!currentResults.length) {
      alert("ظ„ط§ طھظˆط¬ط¯ ظ†طھط§ط¦ط¬ ظ„ظ„طھطµط¯ظٹط±");
      return;
    }

    const selectedCheckboxes = Array.from(
      document.querySelectorAll(".result-checkbox:checked")
    );

    let itemsToExport = [];
    if (selectedCheckboxes.length > 0) {
      itemsToExport = selectedCheckboxes
        .map((cb) => currentResults[parseInt(cb.dataset.index)])
        .filter(Boolean);
    } else {
      const confirmAll = confirm(
        `ظ„ظ… طھظ‚ظ… ط¨طھط­ط¯ظٹط¯ ظ…ظ†طھط¬ط§طھ ظ…ط¹ظٹظ†ط©. ظ‡ظ„ طھط±ط؛ط¨ ظپظٹ طھطµط¯ظٹط± ط¬ظ…ظٹط¹ ط§ظ„ظ…ظ†طھط¬ط§طھ (${currentResults.length} ظ…ظ†طھط¬)طں\n\nظ…ظ„ط§ط­ط¸ط©: ظٹظ…ظƒظ†ظƒ طھط­ط¯ظٹط¯ ظ…ظ†طھط¬ط§طھ ظ…ط¹ظٹظ†ط© ط¹ط¨ط± ظ…ط±ط¨ط¹ط§طھ ط§ظ„ط§ط®طھظٹط§ط± ظپظٹ ط§ظ„ط¬ط¯ظˆظ„ ط£ظˆ ط®ظٹط§ط± 'طھط­ط¯ظٹط¯ ط§ظ„ظƒظ„'.`
      );
      if (!confirmAll) return;
      itemsToExport = currentResults;
    }

    const dataToSend = itemsToExport.map((r) => ({
      name: r.name,
      barcode: r.barcode,
      sku: r.sku || r.barcode,
      price: r.price,
      quantity: r.quantity,
      description: r.description,
      category: r.category || "",
      product_type: r.product_type || "",
      image_url: r.image_url || r.candidates?.[0]?.image_url || "",
      top_title: r.top_title || "",
      status: r.status || "ظ…طھط§ط­",
      no: r.no || r.row,
    }));

    try {
      const res = await fetch("/api/export-salla-template", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          results: dataToSend,
          template_type: templateType,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "ظپط´ظ„ ط§ظ„طھطµط¯ظٹط±");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const prefix = templateType === "update" ? "salla_update" : "salla_new";
      link.download = `${prefix}_products_${Date.now()}.xlsx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("â‌Œ " + e.message);
    }
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // ط¥ط¹ط§ط¯ط© طھط¹ظٹظٹظ†
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function resetAll() {
    if (currentResults.length > 0 && !confirm("ط³ظٹطھظ… ظپظ‚ط¯ط§ظ† ط§ظ„ظ†طھط§ط¦ط¬. ظ…طھط§ط¨ط¹ط©طں"))
      return;

    document.getElementById("upload-panel").classList.remove("hidden");
    document.getElementById("preview-panel").classList.add("hidden");
    document.getElementById("results-panel").classList.add("hidden");
    document.getElementById("progress-panel").classList.add("hidden");
    document.getElementById("sticky-toolbar").classList.add("hidden");
    document.getElementById("excel-file").value = "";

    parsedProducts = [];
    currentResults = [];
    currentPreviewContext = null;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  // Helpers
  // â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
  function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function escapeAttr(text) {
    return String(text || "")
      .replace(/'/g, "\\'")
      .replace(/"/g, "&quot;");
  }
</script>
{% endblock %}
