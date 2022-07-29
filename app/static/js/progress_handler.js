let queuedItemId = (link_id) => `queued-${link_id}`;
let downloadedItemId = (link_id) => `downloaded-${link_id}`;
let progressBarId = (link_id) => `progress-${link_id}`;
let speedLabelId = (link_id) => `speed-${link_id}`;
let etaLabelId = (link_id) => `eta-${link_id}`;

let createText = (text) => document.createTextNode(text);
let createTag = (tag, attributes = {}, ...childs) => {
    let element = document.createElement(tag);

    for (const attr of Object.keys(attributes)) {
        element.setAttribute(attr, attributes[attr]);
    }

    for (const child of childs) {
        element.appendChild(child);
    }

    return element;
}
let getTag = (id) => document.getElementById(id);

let generateQueuedItem = (link_id, title) => {
    return (
        createTag("li", { class: "list-group-item", id: queuedItemId(link_id) },
            createTag("div", { class: "row align-items-center" },
                createTag("div", { class: "col-6 d-flex align-items-center" },
                    createTag("input", { class: "form-check-input me-4", type: "checkbox", value: "" }),
                    createText(title)
                ),
                createTag("div", { class: "col-3" },
                    createTag("div", { class: "progress" },
                        createTag("div", { class: "progress-bar bg-success", id: progressBarId(link_id), role: "progressbar", style: "width: 0%" })
                    )
                ),
                createTag("div", { class: "col-1", id: speedLabelId(link_id) }),
                createTag("div", { class: "col-1", id: etaLabelId(link_id) }),
                createTag("div", { class: "col-1 text-end" },
                    createTag("button", { class: "btn", type: "button" },
                        createTag("i", { class: "bi bi-trash" })
                    )
                )
            )
        )
    )
}
let generateDownloadedItem = (link_id, title) => {
    return (
        createTag("li", { class: "list-group-item", id: downloadedItemId(link_id) },
            createTag("div", { class: "row align-items-center" },
                createTag("div", { class: "col-6 d-flex align-items-center" },
                    createTag("input", { class: "form-check-input me-4", type: "checkbox", value: "" }),
                    createText(title)
                ),
                createTag("div", { class: "col-5" }),
                createTag("div", { class: "col-1 text-end" },
                    createTag("button", { class: "btn", type: "button" },
                        createTag("i", { class: "bi bi-trash" })
                    )
                )
            )
        )
    )
}

let isInt = (value) => {
    if (isNaN(value)) {
        return false;
    }

    let x = parseFloat(value);
    return (x | 0) === x;
}
let humanizeSize = (size) => {
    const units = ["B", "kB", "MB", "GB", "TB"];

    if (size < 0 && !isInt(size)) {
        return "0";
    } else if (size === 0) {
        return `0 ${units[0]}`;
    } else if (size >= 1) {
        let offset = Math.floor(Math.log10(size) / 3);
        if (offset >= units.length) offset = units.length - 1;

        let humanizedSize = (size / Math.pow(1000, offset)).toFixed(1);
        return `${humanizedSize} ${units[offset]}`;
    }
}

class EventListener extends EventSource {
    constructor(endpoint) {
        super(endpoint);
    }
    listen(eventName, callback) {
        super.addEventListener(eventName, e => { callback(JSON.parse(e.data)); });
        return this;
    }

    listenQueued(callback) {
        this.listen("queued", callback);
        return this;
    }

    listenDownloading(callback) {
        this.listen("downloading", callback);
        return this;
    }

    listenExtracting(callback) {
        this.listen("extracting", callback);
        return this;
    }

    listenDownloaded(callback) {
        this.listen("downloaded", callback);
        return this;
    }

    listenNoData(callback) {
        this.listen("no_data", callback);
    }
}

let render = () => {
    const progressListener = new EventListener("progress/");
    progressListener.listenQueued(data => {
        console.log("QUEUED");
        // TODO: for (const id of data) {}
        for (let link_id in data) {
            let queued_item = getTag(queuedItemId(link_id));
            if (queued_item) {
                continue;
            }

            getTag("downloading-list").appendChild(generateQueuedItem(link_id, data[link_id]));
        }
    }).listenDownloading(data => {
        console.log("DOWNLOADING");
        let queued_item = getTag(queuedItemId(data.id));

        if (!queued_item) {
            return;
        }

        getTag(progressBarId(data.id)).style.width = `${data.percent}`;
        getTag(speedLabelId(data.id)).innerHTML = `${humanizeSize(data.speed)}/s`;
        getTag(etaLabelId(data.id)).innerHTML = `${data.eta}s`;
    }).listenExtracting(data => {
        console.log("EXTRACTING");
        if (data.status === 0) {
            getTag(progressBarId(data.id)).className = "progress-bar progress-bar-striped progress-bar-animated";
            getTag(progressBarId(data.id)).width = "100%";
        } else if (data.status === 1) {
            getTag(queuedItemId(data.id)).remove();

            if (!getTag(downloadedItemId(data.id))) {
                getTag("downloaded-list").appendChild(generateDownloadedItem(data.id, data.title));
            }

            if (getTag("downloading-list").children.length === 0) {
                progressListener.close();
            }
        }
    }).listenDownloaded(data => {
        console.log("DOWNLOADED:");
        console.log(data);
        getTag("downloaded-list").appendChild(generateDownloadedItem(data.id, data.title));
    }).listenNoData(_ => {
        console.log("NO DATA");
        progressListener.close();
    });

    // TODO: actually split downloaded and progress endpoints bc during downloading it doesn't list already downlaoded songs :(
}