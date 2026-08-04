// ── Modal ─────────────────────────────────────────────────
// Bootstrap-style modal engine: you author each modal's HTML yourself
// wherever it's needed, then either trigger it declaratively or drive it
// from JS. This file only knows how to show/hide an element by id — it
// never builds modal markup itself.
//
// Declarative trigger (no JS needed):
//   <button data-modal-target="#new-post-modal">New post</button>
//
// Dismiss button inside a modal (closes its nearest modal):
//   <button type="button" data-modal-dismiss>Cancel</button>
//
// Programmatic control:
//   Modal.open('#new-post-modal')
//   Modal.close('#new-post-modal')
//
// Expected markup shape (see templates/partials/new-post-modal.html or the
// delete-confirmation modal in templates/posts/show.html for full examples):
//   <div id="new-post-modal" class="modal hidden fixed inset-0 z-[100] items-center justify-center p-4 bg-ink/50 opacity-0 transition-opacity duration-200">
//     <div data-modal-dialog class="opacity-0 scale-95 translate-y-2 transition-all duration-200 ...">
//       ...your content...
//       <button type="button" data-modal-dismiss>Cancel</button>
//     </div>
//   </div>
//
// The root element (the one carrying the id) doubles as the backdrop:
// clicking it directly — not its children — dismisses the modal, same as
// clicking outside a Bootstrap modal's dialog.
window.Modal = (() => {
  const FOCUSABLE = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

  let openStack = [];

  function resolveEl(idOrSelector) {
    if (idOrSelector instanceof Element) return idOrSelector;
    if (typeof idOrSelector !== 'string') return null;
    const selector = idOrSelector.startsWith('#') ? idOrSelector : `#${idOrSelector}`;
    return document.querySelector(selector);
  }

  function getDialog(modalEl) {
    return modalEl.querySelector('[data-modal-dialog]') || modalEl.firstElementChild;
  }

  function trapFocus(e, modalEl) {
    if (e.key !== 'Tab') return;
    const focusable = Array.from(modalEl.querySelectorAll(FOCUSABLE)).filter((el) => el.offsetParent !== null);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function onKeydown(e) {
    const topId = openStack[openStack.length - 1];
    if (!topId) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      close(topId);
    } else {
      const modalEl = document.getElementById(topId);
      if (modalEl) trapFocus(e, modalEl);
    }
  }

  function onBackdropMousedown(e) {
    if (e.target === e.currentTarget) close(e.currentTarget.id);
  }

  function open(idOrSelector, config = {}) {
    const modalEl = resolveEl(idOrSelector);
    if (!modalEl || !modalEl.id || openStack.includes(modalEl.id)) return;

    const dialog = getDialog(modalEl);

    modalEl._lastFocused = document.activeElement;
    openStack.push(modalEl.id);
    document.body.classList.add('overflow-hidden');

    modalEl.classList.remove('hidden');
    modalEl.classList.add('flex');
    modalEl.addEventListener('mousedown', onBackdropMousedown);

    if (config.onDismis && typeof config.onDismis === 'function') {
      modalEl._dismissHandler = config.onDismis
    }

    if (!modalEl._dismissHandler) {
      modalEl._dismissHandler = () => close(modalEl.id);
    }
    modalEl.querySelectorAll('[data-modal-dismiss]').forEach((btn) => {
      btn.addEventListener('click', modalEl._dismissHandler);
    });

    if (openStack.length === 1) document.addEventListener('keydown', onKeydown, true);

    requestAnimationFrame(() => {
      modalEl.classList.remove('opacity-0');
      if (dialog) dialog.classList.remove('opacity-0', 'scale-95', 'translate-y-2');
      const autofocusEl = modalEl.querySelector('[autofocus]');
      const target = autofocusEl || dialog || modalEl;
      if (target && typeof target.focus === 'function') target.focus();
    });
  }

  function close(idOrSelector) {
    const modalEl = resolveEl(idOrSelector);
    if (!modalEl || !openStack.includes(modalEl.id)) return;

    const dialog = getDialog(modalEl);

    modalEl.classList.add('opacity-0');
    if (dialog) dialog.classList.add('opacity-0', 'scale-95', 'translate-y-2');

    setTimeout(() => {
      modalEl.classList.add('hidden');
      modalEl.classList.remove('flex');
      modalEl.removeEventListener('mousedown', onBackdropMousedown);

      openStack = openStack.filter((id) => id !== modalEl.id);
      if (openStack.length === 0) {
        document.removeEventListener('keydown', onKeydown, true);
        document.body.classList.remove('overflow-hidden');
      }
      if (modalEl._lastFocused && typeof modalEl._lastFocused.focus === 'function') {
        modalEl._lastFocused.focus();
      }
    }, 200);
  }

  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-modal-target]');
    if (trigger) open(trigger.getAttribute('data-modal-target'));
  });

  return { open, close };
})();


