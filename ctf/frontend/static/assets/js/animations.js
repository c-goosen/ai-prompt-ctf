/*
 * Animations adapted from Watermelon UI (https://ui.watermelon.sh, MIT):
 * fluid-tabs, inline-toast, labeled-progress-indicator, copy-confirm,
 * shimmer-button. Ported from motion/react to vanilla JS; styles live in
 * ../css/animations.css.
 *
 * htmx 4 dispatches its events on the source element with detail = {ctx},
 * so the element is evt.target (there is no detail.elt / detail.target).
 */
(function () {
    if (window.__pwnAnimations) {
        return;
    }
    window.__pwnAnimations = true;

    const reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;
    const CHAT_URL = "/v1/chat/completions";

    function restartAnimation(el, className) {
        el.classList.remove(className);
        void el.offsetWidth; // force reflow so the animation replays
        el.classList.add(className);
    }

    function isChatRequest(elt) {
        return Boolean(
            elt && elt.getAttribute && elt.getAttribute("hx-post") === CHAT_URL
        );
    }

    /* watermelon: fluid-tabs (sidebar sliding pill) */

    function navItems() {
        return Array.from(
            document.querySelectorAll(".chats-levels > .level-menu[hx-get]")
        );
    }

    function normalizePath(path) {
        return path === "/" || path === "/chat" ? "/ctf" : path;
    }

    function ensurePill() {
        const nav = document.querySelector(".chats-levels");
        if (!nav) {
            return null;
        }
        let pill = nav.querySelector(".nav-pill");
        if (!pill) {
            pill = document.createElement("span");
            pill.className = "nav-pill";
            pill.setAttribute("aria-hidden", "true");
            nav.prepend(pill);
        }
        return pill;
    }

    function setActive(item, pulse) {
        const pill = ensurePill();
        if (!pill) {
            return;
        }
        navItems().forEach(function (el) {
            el.classList.toggle("is-active", el === item);
        });
        if (!item) {
            pill.classList.remove("is-visible");
            return;
        }
        const firstPlacement = !pill.classList.contains("is-visible");
        if (firstPlacement) {
            // Appear in place rather than springing in from the top.
            pill.style.transition = "none";
        }
        pill.style.transform = "translateY(" + item.offsetTop + "px)";
        pill.style.height = item.offsetHeight + "px";
        pill.classList.add("is-visible");
        if (firstPlacement) {
            void pill.offsetWidth;
            pill.style.transition = "";
        }
        if (pulse && !reduceMotion) {
            restartAnimation(item, "is-pulsing");
            item.addEventListener(
                "animationend",
                function () {
                    item.classList.remove("is-pulsing");
                },
                { once: true }
            );
        }
    }

    function syncActive() {
        const path = normalizePath(window.location.pathname);
        const item = navItems().find(function (el) {
            return normalizePath(el.getAttribute("hx-get")) === path;
        });
        setActive(item || null, false);
    }

    document.addEventListener("click", function (evt) {
        const item = evt.target.closest(".chats-levels > .level-menu[hx-get]");
        if (item) {
            setActive(item, true);
        }
    });
    window.addEventListener("popstate", syncActive);
    window.addEventListener("resize", syncActive);

    /* watermelon: labeled-progress-indicator (chat loader) */

    const LOADER_LABELS = [
        "Thinking…",
        "Checking guardrails…",
        "Calling tools…",
        "Sending…",
    ];
    let loaderTimer = null;

    function setLoaderLabel(text) {
        const label = document.querySelector(".chat-loader .loader-label");
        if (!label) {
            return;
        }
        label.textContent = text;
        if (!reduceMotion) {
            restartAnimation(label, "is-changing");
        }
    }

    function startLoader() {
        stopLoader();
        if (reduceMotion) {
            setLoaderLabel("Sending…");
            return;
        }
        let index = 0;
        setLoaderLabel(LOADER_LABELS[index]);
        loaderTimer = window.setInterval(function () {
            index = (index + 1) % LOADER_LABELS.length;
            setLoaderLabel(LOADER_LABELS[index]);
        }, 1600);
    }

    function stopLoader() {
        if (loaderTimer !== null) {
            window.clearInterval(loaderTimer);
            loaderTimer = null;
        }
    }

    /* watermelon: inline-toast (chat message entrance) */

    // Only bubbles that arrive from a chat POST animate; history loads and
    // page navigation insert their bubbles without replaying an entrance.
    let animateNewMessagesUntil = 0;

    document.addEventListener("htmx:before:request", function (evt) {
        if (isChatRequest(evt.target)) {
            startLoader();
        }
    });
    document.addEventListener("htmx:after:request", function (evt) {
        if (isChatRequest(evt.target)) {
            animateNewMessagesUntil = performance.now() + 1500;
        }
    });
    document.addEventListener("htmx:finally:request", function (evt) {
        if (isChatRequest(evt.target)) {
            stopLoader();
        }
    });
    document.addEventListener("htmx:after:swap", syncActive);

    function animateMessage(chat, index) {
        chat.style.setProperty("--i", Math.min(index, 6));
        chat.classList.add("msg-enter");
        chat.addEventListener(
            "animationend",
            function () {
                chat.classList.remove("msg-enter");
                chat.style.removeProperty("--i");
            },
            { once: true }
        );
    }

    /* watermelon: copy-confirm (copy buttons) */

    function renderCopyState(btn, state) {
        const label = { idle: "Copy", copied: "Copied", failed: "Copy failed" }[
            state
        ];
        btn.classList.toggle("is-copied", state === "copied");
        btn.setAttribute(
            "aria-label",
            state === "copied" ? "Copied to clipboard" : "Copy to clipboard"
        );

        const icon = document.createElement("i");
        icon.className =
            "fa-solid copy-icon " +
            (state === "copied" ? "fa-check" : "fa-copy");
        icon.setAttribute("aria-hidden", "true");

        const text = document.createElement("span");
        text.className = "copy-text";
        text.setAttribute("aria-hidden", "true");
        Array.from(label).forEach(function (char, i) {
            const span = document.createElement("span");
            span.className = "copy-char";
            span.style.setProperty("--i", i);
            span.textContent = char === " " ? " " : char;
            text.append(span);
        });

        btn.replaceChildren(icon, text);
    }

    function addCopyButtons(root) {
        if (!root.querySelectorAll) {
            return;
        }
        const pres = root.matches && root.matches(".chat-bubble pre")
            ? [root]
            : root.querySelectorAll(".chat-bubble pre");
        pres.forEach(function (pre) {
            if (pre.classList.contains("has-copy")) {
                return;
            }
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "copy-btn";
            renderCopyState(btn, "idle");
            pre.classList.add("has-copy");
            pre.append(btn);
        });
    }

    function textToCopy(btn) {
        if (btn.dataset.copy !== undefined) {
            return btn.dataset.copy;
        }
        const pre = btn.closest("pre");
        if (!pre) {
            return "";
        }
        const clone = pre.cloneNode(true);
        clone.querySelectorAll(".copy-btn").forEach(function (b) {
            b.remove();
        });
        return clone.textContent.trim();
    }

    async function copyText(text) {
        // navigator.clipboard needs a secure context, and the app is often
        // served over plain http on 0.0.0.0.
        if (navigator.clipboard && window.isSecureContext) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (err) {
                // fall through to the legacy path
            }
        }
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.append(textarea);
        textarea.select();
        let copied = false;
        try {
            copied = document.execCommand("copy");
        } catch (err) {
            copied = false;
        }
        textarea.remove();
        return copied;
    }

    document.addEventListener("click", async function (evt) {
        const btn = evt.target.closest(".copy-btn");
        if (!btn) {
            return;
        }
        evt.preventDefault();
        const copied = await copyText(textToCopy(btn));
        btn.classList.toggle("is-animating", !reduceMotion);
        renderCopyState(btn, copied ? "copied" : "failed");
        window.clearTimeout(btn.__copyResetTimer);
        btn.__copyResetTimer = window.setTimeout(function () {
            renderCopyState(btn, "idle");
        }, 1800);
    });

    /* Watch the swapped-in content for new bubbles and rendered code blocks. */

    function onMutations(records) {
        const animate =
            !reduceMotion && performance.now() < animateNewMessagesUntil;
        let index = 0;
        records.forEach(function (record) {
            record.addedNodes.forEach(function (node) {
                if (node.nodeType !== Node.ELEMENT_NODE) {
                    return;
                }
                if (
                    animate &&
                    node.matches(".chat") &&
                    node.closest(".chat-history")
                ) {
                    animateMessage(node, index);
                    index += 1;
                }
                addCopyButtons(node);
            });
        });
    }

    function init() {
        syncActive();
        addCopyButtons(document);
        const panel = document.querySelector(".right-panel");
        if (panel) {
            new MutationObserver(onMutations).observe(panel, {
                childList: true,
                subtree: true,
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
