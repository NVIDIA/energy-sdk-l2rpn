<template>
    <div>
        <v-row no-gutters>
            <div class="overline mb-1">
                Recommend Actions [3 of {{nactions}}]
            </div>
        </v-row>
        <v-row no-gutters align="center">
            Hot Substations: <v-chip class="ml-1" v-for="sub in hot_subs" label small color="red">
                sub {{sub[0]}} [{{sub[1]}}]
            </v-chip>
        </v-row>
        <v-row no-gutters align="center">
            <v-col>
                <v-tooltip top>
                    <template v-slot:activator="{ on, attrs }">
                        <v-switch v-on="on" small v-model="randomize"></v-switch>
                    </template>
                    <span>Randomize search: {{randomize}}</span>
                </v-tooltip>
            </v-col>
            <v-col v-for="perc in [1, 20, 50, 100]">
                <v-btn small class="mr-1" @click="search_actions(perc)">{{perc}}%</v-btn>
            </v-col>

            <v-col cols=auto class="ml-2">
                <v-tooltip top v-for="act in recommended_acts">
                    <template v-slot:activator="{ on, attrs }">
                        <v-chip class="mr-1" small :color="act.color" @click="take_action(act.aid)"
                            @mouseover="highlight_elements(act.aid)" @mouseout="unhighlight_elements">

                            <v-icon left small v-on="on">
                                mdi-information
                            </v-icon>
                            ρ={{act.rho}}
                        </v-chip>
                    </template>

                    <kbd>[{{act.aid}}] ρ={{act.rho}}\n{{act.info}}</kbd>
                </v-tooltip>
            </v-col>
        </v-row>
        <v-row no-gutters class='mt-1'>
            <kbd v-if="act_search_status">{{act_search_status}}</kbd>
        </v-row>
    </div>
</template>