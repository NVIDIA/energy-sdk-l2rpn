<template>
    <div style="overflow: auto;">
        <v-row no-gutters align="center">
            <div class="overline" @click="showfig=!showfig">
                Plots</div>
            <v-icon small @click="showfig=!showfig" class="ma-1">
                {{showfig ? 'mdi-eye' : 'mdi-eye-off'}}
            </v-icon>
        </v-row>
        <v-row no-gutters align="center" v-if="showfig">
            <v-col cols=auto>Group by:</v-col>
            <v-col>
                <v-chip small label outlined class="ma-1" @click="set_plot_gby(gby)"
                    v-for="gby in ['all', 'gen type', 'gen type (100%)']">
                    {{gby}}
                </v-chip>
            </v-col>

            <v-col cols=auto>
                <v-chip small outlined label @click="update_plot">
                    <v-icon small>
                        mdi-reload
                    </v-icon>
                </v-chip>
            </v-col>
        </v-row>
        <div style="overflow: auto;" v-if="showfig">
            <plt-figure></plt-figure>
        </div>
    </div>
</template>