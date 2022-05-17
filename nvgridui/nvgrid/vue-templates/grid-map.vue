<template>
    <div id="printcontent" ref="printcontent" v-resize="wresize" @click="" @keydown="lc_key($event.key)">
        <grid-map></grid-map>
    </div>
</template>

<script>
    module.exports = {
        methods: {
            wresize() {
                this.wsz = { x: window.innerWidth, y: window.innerHeight }
            }
        }
    }
</script>