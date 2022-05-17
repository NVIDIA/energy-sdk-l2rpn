<template>
    <!-- <div v-resize="app_resize(wresize())"> -->
    <div v-resize="wresize">

        <v-app-bar dense dark src="/resources/nvidia-logo.png">
            <v-app-bar-nav-icon></v-app-bar-nav-icon>
            <v-toolbar-title>nvPowerGrid</v-toolbar-title>
            <v-spacer></v-spacer>

            <v-dialog v-model="output_dialog" max-width="1000">
                <template v-slot:activator="{ on, attrs }">
                    <v-btn outlined small v-bind="attrs" v-on="on">
                        Output
                    </v-btn>
                </template>
                <div style="z-index:99">
                    <v-card>
                        <v-card-title class="text-h5 grey lighten-2">
                            App Text Output (Errors)
                            <v-spacer></v-spacer>
                            <v-btn small outlined @click="clear_output">clear</v-btn>
                        </v-card-title>
                        <v-row class="pa-2" align="center" no-gutters>
                            <v-col>
                                <app-output></app-output>
                            </v-col>

                        </v-row>
                    </v-card>
                </div>
            </v-dialog>

        </v-app-bar>
        <v-row no-gutters class="pa-1" v-show="!output_dialog">
            <v-col cols=8>
                <v-card class="pa-1">
                    <left-card />
                </v-card>
            </v-col>
            <v-col cols=4>
                <v-card class="ml-1 pa-1">
                    <right-card></right-card>
                </v-card>
            </v-col>

        </v-row>
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