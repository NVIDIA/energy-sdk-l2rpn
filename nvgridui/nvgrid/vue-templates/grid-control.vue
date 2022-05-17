<template>
    <!-- <div style="background-color: gray"> -->
    <div>
        <v-card flat class="ma-1 pa-0">
            <v-row no-gutters align="center">
                <v-col cols=auto class="mr-1">
                    <v-chip label outlined class="pa-1">
                        <v-icon small>
                            mdi-office-building
                        </v-icon>
                        <span class="mr-1">{{nsubs}}</span>
                        <v-divider vertical></v-divider>
                        <v-icon small class="ml-1">
                            mdi-transmission-tower
                        </v-icon>{{nlines}}
                    </v-chip>
                </v-col>
                <v-col>
                    <v-select label="Environment Dataset" :items="environments" item-text="text" item-value="value"
                        v-model="env_name">

                    </v-select>
                </v-col>
                <v-col cols=auto class="ml-1">
                    <v-btn small @click="load_env" :loading="env_loading">load env</v-btn>
                </v-col>
            </v-row>
            <v-row no-gutters align="center">

                <v-col>
                    <v-chip label class="mr-1">{{date}}</v-chip>
                    <v-chip label :color="maxrho_color" class="mr-1">ρ={{maxrho}}</v-chip>
                    <v-chip label>{{steps}}</v-chip>
                    <v-chip label>{{scenario}}</v-chip>
                </v-col>
                <v-col cols=auto>
                    <v-tooltip top>
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn small @click="restart" v-on="on">
                                <v-icon>mdi-reload</v-icon>
                            </v-btn>
                        </template>
                        <span>Reset environment</span>
                    </v-tooltip>
                </v-col>

            </v-row>
        </v-card>

        <v-card flat class="ma-1 pa-1">
            <!-- Plots -->
            <v-row no-gutters>
                <plots-control></plots-control>
            </v-row>

            <v-row no-gutters>
                <div class="overline mb-4">
                    Map Controls
                </div>
            </v-row>
            <v-row no-gutters>
                <v-btn small @click="animate_lines" :loading="animation_loading">
                    <v-icon small left>
                        {{animated_lines ? 'mdi-check-circle-outline' :'mdi-circle-outline'}}
                    </v-icon>

                    {{animated_lines ? 'stop animation':'animate lines' }}
                </v-btn>
                <v-btn class="ml-1" small @click="center_map">center</v-btn>

            </v-row>

        </v-card>

        <v-row no-gutters>
            <v-col>
                <v-card flat class="ma-1 pa-1">
                    <v-row no-gutters>
                        <div class="overline mb-1">
                            sim Controls
                        </div>
                    </v-row>

                    <!-- DoNothing Actions -->
                    <v-row align="center" class="ma-0">
                        <v-col cols=8>
                            <v-progress-linear v-model="step_progress"></v-progress-linear>
                            <v-text-field type=number v-model="steps2attempt" label="Attempt # steps"></v-text-field>

                        </v-col>
                        <v-cols cols=4>
                            <v-btn small @click="attempt_nsteps">Attempt</v-btn>
                        </v-cols>
                    </v-row>

                    <!-- Redispatch -->
                    <v-row no-gutters>
                        <div class="overline">
                            redispatch
                        </div>
                        <!-- </v-row>
                    <v-row no-gutters> -->
                        <div @mouseover="highlight_elements({'gens':[selected_gen.gid]})"
                            @mouseout="unhighlight_elements" class="mb-4">
                            <v-chip label outlined small>
                                {{selected_gen.info}}
                            </v-chip>
                            <v-chip small v-if="selected_gen.redispatchable"
                                @click="redispatch([selected_gen.gid,selected_gen.maxup/100])">
                                +{{selected_gen.maxup/100}} MW
                            </v-chip>
                            <v-chip small v-if="selected_gen.redispatchable"
                                @click="redispatch([selected_gen.gid,-selected_gen.maxdown/100])">
                                -{{selected_gen.maxdown/100}} MW
                            </v-chip>
                        </div>
                    </v-row>

                    <!-- Reconnect Lines -->

                    <v-row no-gutters>
                        <div class="overline mb-4">
                            disconnected lines
                        </div>
                        <!-- </v-row>
                    <v-row no-gutters> -->
                        <v-chip small @mouseover="highlight_elements({'lines':[line.lid]})"
                            @mouseout="unhighlight_elements" v-for="line in disconnected_lines"
                            :color="line.cdt>0 ? '' : 'red'" @click="reconnect_line(line.lid)">
                            {{line.lid}} [{{line.cdt}}]
                        </v-chip>
                    </v-row>

                    <!-- Actions on Lines -->
                    <v-row no-gutters>
                        <div class="overline mb-1">
                            actions on selected line(s)
                        </div>
                    </v-row>
                    <v-row no-gutters class="mb-5">
                        <v-tooltip top v-for="line in selected_lines">
                            <template v-slot:activator="{ on, attrs }">
                                <v-chip label small @mouseover="highlight_elements({'lines':[line.lid]})"
                                    @mouseout="unhighlight_elements" :color="line.cdt>0 ? '' : 'red'"
                                    @click="disconnect_line(line.lid)">
                                    <v-icon left small v-on="on" @mouseover="sim_disconnect_line(line.lid)">
                                        mdi-information
                                    </v-icon>

                                    Disconnect line {{line.lid}}
                                </v-chip>
                            </template>

                            <kbd>{{line.info}}</kbd>
                        </v-tooltip>
                    </v-row>
                    <!-- Action Recommender -->
                    <v-row align="center" class="ma-0">
                        <action-recommender></action-recommender>
                    </v-row>

                </v-card>
            </v-col>
        </v-row>

        <v-row no-gutters>
            <v-col>
                <v-card flat class="ma-1 pa-1">
                    <v-row no-gutters>
                        <div class="overline mb-4">
                            logs
                        </div>


                    </v-row>

                    <v-select label="Show # logs" v-model="show_nlogs" :items="[0, 1, 2, 3, 4]">
                    </v-select>
                    <v-row no-gutters v-for="(log, index) in logs" class="ma-1" v-if="10-index <= show_nlogs">
                        <kbd>{{log}}</kbd>
                    </v-row>
                </v-card>
            </v-col>
        </v-row>


    </div>
</template>

<script>
    module.exports = {
        methods: {

        }
    }
</script>