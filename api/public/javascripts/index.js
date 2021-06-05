const selects = document.getElementsByTagName("select");

function onchangeEvent(event) {
    const prevSelectIndex = this.prevSelectIndex || 0;
    for (const select of selects) {
        if (prevSelectIndex)
            select[prevSelectIndex].hidden = false;
        for (const option of select) {
            if (option.value == this.value)
                option.hidden = true;
        }
    }
    this.prevSelectIndex = this.selectedIndex;
}


for (const currentSelect of selects) {
    currentSelect.onchange = onchangeEvent;
}
