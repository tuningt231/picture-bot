const BASE_URL = 'http://localhost:8000';

export const API = {
    async getConfig() {
        const to = new Date();
        const timespanHours = 5;
        const from = new Date(to.getTime() - timespanHours * 3_600_000);
        const params = new URLSearchParams({
            from_date: from.toISOString(),
            to_date: to.toISOString(),
        });
        const resp = await fetch(`${BASE_URL}/pictures?${params}`);
        if (!resp.ok) throw new Error(`Config fetch failed: ${resp.status}`);
        return resp.json(); // [{id, label, type, accepted_at}]
    },

    async getImageBlob(id) {
        const resp = await fetch(`${BASE_URL}/pictures/${id}/download`);
        if (!resp.ok) throw new Error(`Image ${id} fetch failed: ${resp.status}`);
        return URL.createObjectURL(await resp.blob());
    },
};
