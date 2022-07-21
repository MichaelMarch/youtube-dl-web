let generate_downloading_item = (data) => `<li class="list-group-item" id="downloading-${data.id}">
    <div class="row align-items-center">
        <div class="col-6 d-flex align-items-center">
            <input class="form-check-input me-4" type="checkbox" value="" />${data.title}
        </div>
        <div class="col-3">
            <div class="progress">
                <div class="progress-bar bg-success" id="progress-${data.id}" role="progressbar" style="width: ${data.percent}%"></div>
            </div>
        </div>
        <div class="col-1" id="speed-${data.id}">${humanize_size2(data.speed)}/s</div>
        <div class="col-1" id="eta-${data.id}">${data.eta}s</div>
        <div class="col-1 text-end">
            <button class="btn" type="button">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    </div>
</li>`

let generate_downloaded_item = (data) => `<li class="list-group-item" id="downloaded-${data.id}">
    <div class="row align-items-center">
        <div class="col-6 d-flex align-items-center">
            <input class="form-check-input me-4" type="checkbox" value="" />
            ${data.title}
        </div>
        <div class="col-5"></div>
        <div class="col-1 text-end">
            <button class="btn" type="button">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    </div>
</li>
`

let humanize_size2 = (size) => {
    const units = ["B", "kB", "MB", "GB", "TB"]
    let offset = Math.ceil((Math.floor(Math.log10(size)) + 1) / 3) - 1

    return `${(size / Math.pow(1000, offset)).toFixed(1)} ${units[offset]}`
}

let render = () => {
    const progress_source = new EventSource("progress/")

    progress_source.addEventListener("downloading", event => {
        let data = JSON.parse(event.data)
        let label = document.getElementById(`downloading-${data.id}`)

        if (label) {
            document.getElementById(`progress-${data.id}`).style.width = `${data.percent}%`

            document.getElementById(`speed-${data.id}`).innerHTML = `${humanize_size2(data.speed)}/s`
            document.getElementById(`eta-${data.id}`).innerHTML = `${data.eta}s`
        } else {
            document.getElementById("downloading-list").innerHTML += generate_downloading_item(data)
        }
    })

    progress_source.addEventListener("extracting", event => {
        let data = JSON.parse(event.data)

        if (data.status === 0) {
            document.getElementById(`progress-${data.id}`).className = "progress-bar progress-bar-striped progress-bar-animated"
        } else if (data.status === 1) {
            const finish_source = new EventSource(`finish/${data.id}`)

            finish_source.onmessage = (event) => {
                if (event.data === "1") {
                    progress_source.close()
                }
                finish_source.close()
            }
            document.getElementById(`downloading-${data.id}`).remove()

            if (!document.getElementById(`downloaded-${data.id}`)) {
                document.getElementById("downloaded-list").innerHTML += generate_downloaded_item(data)
            }
        }
    })

    progress_source.addEventListener("no_data", _ => { progress_source.close() })

    const downloaded_source = new EventSource("downloaded/")

    downloaded_source.addEventListener("downloaded", event => {
        let data = JSON.parse(event.data)

        document.getElementById("downloaded-list").innerHTML += generate_downloaded_item(data)
    })

    downloaded_source.addEventListener("no_data", _ => { downloaded_source.close() })
}