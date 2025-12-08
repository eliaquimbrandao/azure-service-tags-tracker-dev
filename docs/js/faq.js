document.addEventListener('DOMContentLoaded', () => {
    const faqCards = document.querySelectorAll('[data-faq]');

    faqCards.forEach((card, index) => {
        const toggleButton = card.querySelector('.faq-toggle');
        const body = card.querySelector('.faq-body');

        if (!toggleButton || !body) {
            return;
        }

        const panelId = body.id || `faq-panel-${index}`;
        body.id = panelId;
        toggleButton.setAttribute('aria-controls', panelId);
        const isInitiallyExpanded = toggleButton.getAttribute('aria-expanded') === 'true';
        card.classList.toggle('expand', isInitiallyExpanded);
        body.hidden = !isInitiallyExpanded;

        toggleButton.addEventListener('click', () => {
            const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';
            toggleButton.setAttribute('aria-expanded', (!isExpanded).toString());
            body.hidden = isExpanded;
            card.classList.toggle('expand', !isExpanded);
        });
    });
});
