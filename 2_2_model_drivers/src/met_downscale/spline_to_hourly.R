spline_to_hourly <- function(df,VarNamesStates){
  # --------------------------------------
  # purpose: interpolates debiased forecasts from 6-hourly to hourly
  # Creator: Laura Puckett, December 16 2018
  # --------------------------------------
  # @param: df, a dataframe of debiased 6-hourly forecasts

  interpolate <- function(jday, var){
    result <- splinefun(jday, var, method = "monoH.FC")
    return(result(seq(min(as.numeric(jday)), max(as.numeric(jday)), 1/24)))
  }
  

  
  t0 = min(df$timestamp)
  df <- df %>%
    mutate(days_since_t0 = difftime(.$timestamp, t0, units = "days"))
  
  if("dscale.member" %in% colnames(df)){
    by.ens <- df %>% 
      group_by(NOAA.member, dscale.member)
  }else{
    by.ens <- df %>% 
      group_by(NOAA.member)
    }
  
  interp.df.days <- by.ens %>% do(days = seq(min(df$days_since_t0), as.numeric(max(df$days_since_t0)), 1/24))
  interp.df <- interp.df.days
  
  for(Var in 1:length(VarNamesStates)){
    assign(paste0("interp.df.",VarNamesStates[Var]), do(by.ens, var = interpolate(.$days_since_t0,unlist(.[,VarNamesStates[Var]]))) %>% plyr::rename(c("var" = VarNamesStates[Var])))
    if("dscale.member" %in% colnames(df)){
        interp.df <- inner_join(interp.df, get(paste0("interp.df.",VarNamesStates[Var])), by = c("NOAA.member", "dscale.member"))
    }else{
      interp.df <- inner_join(interp.df, get(paste0("interp.df.",VarNamesStates[Var])), by = c("NOAA.member"))
    } 
  }

  # converting from time difference back to timestamp
  interp.df  = interp.df %>%
    unnest(c("days", all_of(VarNamesStates))) %>%
    dplyr::mutate(timestamp = as_datetime(t0 + days, tz = attributes(t0)$tzone))
  return(interp.df)
}

