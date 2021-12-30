/*****************************main.c***************************/

#define MAIN
#include "satpos.h"
#undef MAIN

#include "sgp4ext.h"
#include "sgp4unit.h"
#include "sgp4io.h"

/**************************************************************/
/* All internal time is UTC.  Some I/O in local */
// https://mycoordinates.org/tracking-satellite-footprints-on-earth’s-surface/

#undef VERBOSE
int main(int argc, char *argv[])
{
  int argSC=0, argTLE=0, i, j, k, n, valid, verbose;
  char TLEprefix[25], TLEFile[100], SCName[40], SCSearch[10], line[100];
  char outname[70], outsatpos[70];
  const char * monstr[] = {"NULL", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
  double period, timeconv[3], lngconv[3];
  FILE *fp, *outfile;
  struct observer obs, subsat, start;
  char str[2];
  double ro[3];
  double vo[3];
  char typeinput, typerun, opsmode;
  gravconsttype  whichconst;
  int whichcon;
  // ----------------------------  locals  -------------------------------
  double p, a, ecc, incl, node, argp, nu, m, arglat, truelon, lonper;
  double sec,  jd, rad, tsince, startmfe, stopmfe, deltamin, jdstart, jdstop;
  double tumin, mu, radiusearthkm, xke, j2, j3, j4, j3oj2;
  int  year, mon, day, hr, min, isec, msec;
  char longstr1[130];
  typedef char str3[4];
  char longstr2[130];
  elsetrec satrec;

  rad = 180.0 / pi;
  verbose = 0;  // Make part of argv
  // ------------------------  implementation   --------------------------

  readObserver(&obs, verbose);

  if (verbose)
    printf("%s:  ", SGP4Version);
  if (argc > 1)
  {
    argTLE = 1;
    strcpy(TLEprefix, argv[1]);
  }
  if (argc > 2)
  {
    argSC = 1;
    sscanf(argv[2], "%d", &k);
  }

  // Get satellite TLE's
  if (!argTLE)
  {
    sprintf(line,"ls -1 %s/*.tle",obs.TLEpath);
    printf("------TLE files------\n");
    system(line);
    printf("\t--------> TLE Filename (leave off the path and .tle):  ");
    scanf("%s",TLEprefix);
  }
  sprintf(TLEFile,"%s/%s.tle",obs.TLEpath,TLEprefix);

  fp=fopen(TLEFile,"r");
  if (fp==NULL)
  {
    printf("%s not found.\n",TLEFile);
    exit(1);
  }
  if (!argSC)
  {
    i=0;
    printf("\n\nSatellites...\n");
    while(!feof(fp))
    {
      getline(fp,SCName,29);
      getline(fp,longstr1,100);
      n=getline(fp,longstr2,100);
      ++i;
      if (n > 10)
        printf("\t%d %s\n",i,SCName);
    }
    rewind(fp);
    printf("Input spacecraft number:  ");
    scanf("%d",&k);
  }
  for(i=0;i<k;++i)
  {
    getline(fp, SCName, 30);
    getline(fp, longstr1, 110);
    getline(fp, longstr2, 110);
  }
  fclose(fp);
  sprintf(outname, "sp_%s%07d.out", TLEprefix, k);
  for(i=strlen(SCName)-1;isspace(SCName[i]);--i)
    SCName[i]='\0';
  printf("\r%s    (%s)                               ",outname, SCName);
  if (verbose)
    printf("\n");

  //opsmode = 'a' best understanding of how afspc code works
  //opsmode = 'i' improved sgp4 resulting in smoother behavior
  opsmode = 'a';
  //typeinput = 'm' input start stop mfe
  //typeinput = 'e' input start stop ymd hms
  //typeinput = 'd' input start stop yr dayofyr
  typeinput = 'e';
  typerun = 'c';  // use 'c' (see testcpp.cpp) to just read in tle's.  start/stop gets set below (so overwrites the 'c' settings in sgp4io)

  whichcon = 84;
  if (whichcon == 721) whichconst = wgs72old;
  if (whichcon == 72) whichconst = wgs72;
  if (whichcon == 84) whichconst = wgs84;

  getgravconst(whichconst, tumin, mu, radiusearthkm, xke, j2, j3, j4, j3oj2);

  // ---------------- setup files for operation ------------------
  outfile = fopen(outname, "w");

  // convert the char string to sgp4 elements
  // includes initialization of sgp4
  twoline2rv(longstr1, longstr2, typerun, typeinput, opsmode, whichconst, startmfe, stopmfe, deltamin, satrec);

  // This is pulled out of sgp4io.cpp to change the start/stop times
  jday( obs.tstart.Year,obs.tstart.Month,obs.tstart.Day,obs.tstart.Hour,obs.tstart.Minute,obs.tstart.Second,jdstart );
  jday( obs.tstop.Year,obs.tstop.Month,obs.tstop.Day,obs.tstop.Hour,obs.tstop.Minute,obs.tstop.Second, jdstop );
  startmfe = (jdstart - satrec.jdsatepoch) * 1440.0;
  stopmfe  = (jdstop - satrec.jdsatepoch) * 1440.0;
  deltamin = obs.tstep;
  if (verbose)
  {
    if (startmfe < 0.0)
      printf("WARNING: TLEs start after observing epoch (%lf days).\n",startmfe/1440.0);
  }
  if (fabs(startmfe/1440.0) > 7.5)
    printf("WARNING: TLEs are over a week off (%lf days).\n",startmfe/1440.0);
  // call the propagator to get the initial state vector value
  sgp4 (whichconst, satrec,  0.0, ro,  vo);

  jd = satrec.jdsatepoch;
  invjday( jd, year,mon,day,hr,min,sec );
  if (verbose)
  {
    printf("stk.v.4.3 \n"); // must use 4.3...
    printf("ScenarioEpoch:  %3i %3s%5i%3i:%2i:%12.9f \n",day,monstr[mon],year,hr,min,sec);
    printf("CoordinateSystem:  TEME-to-PEF\n\n");  //TEME (True Equator Mean Equinox) - PEF (Pseudo Earth Fixed)
  }
  // First do it for 'start'
  tsince = startmfe;
  sgp4 (whichconst, satrec,  tsince, ro,  vo);
  teme2pef(obs,jdstart,ro,&start);
  period = 2.0*pi/satrec.no;

  if (verbose)
  {
    printf("Period: %.3f [min]\n", period);
    printf("Starting Position:\n\t(x,y,z,r):  %lf, %lf, %lf, %lf\n",ro[0],ro[1],ro[2],start.alt);
    printf("\t(sub_lng, sub_lat, h):  %lf, %lf, %lf\n",start.lng,start.lat,start.h);
  }

  // Write header
  fprintf(outfile, "#spacecraft name: %s\n", SCName);
  fprintf(outfile, "#satnum: %ld\n", satrec.satnum);
  fprintf(outfile, "#observer: %s\n", obs.Code);
  fprintf(outfile, "#file and entry number: %s %d\n", TLEFile, k);
  fprintf(outfile, "#line1: %s\n", longstr1);
  fprintf(outfile, "#line2: %s\n", longstr2);
  fprintf(outfile, "#period: %12.9f min\n", period);
  fprintf(outfile, "#starting x y z r: %lf %lf %lf %lf\n",ro[0],ro[1],ro[2],start.alt);
  fprintf(outfile, "#starting lon lat h: %lf %lf %lf\n",start.lng,start.lat,start.h);
  fprintf(outfile, "#starting epoch: %02d-%02d-%d %02d:%02d:%02d\n", obs.tstart.Year, obs.tstart.Month, obs.tstart.Day, obs.tstart.Hour, obs.tstart.Minute, int(obs.tstart.Second));
  fprintf(outfile, "#scenario epoch:  %lf jd\n",satrec.jdsatepoch);

  // check so the first value isn't written twice
  if ( fabs(tsince) > 1.0e-8 )
    tsince = tsince - deltamin;
  lngconv[0] = 999.9;
  // ----------------- loop to perform the propagation ----------------
  while ((tsince < stopmfe) && (satrec.error == 0))
  {
    tsince = tsince + deltamin;
    if(tsince > stopmfe)
      tsince = stopmfe;
    sgp4(whichconst, satrec,  tsince, ro,  vo);

    if (satrec.error > 0)
      printf("# *** error: t:= %f *** code = %3d\n",satrec.t, satrec.error);
    if (satrec.error == 0)
    {
      jd = satrec.jdsatepoch + tsince/1440.0;
      invjday(jd, year,mon,day,hr,min, sec);
      teme2pef(obs, jd, ro, &subsat);
      lngconv[1] = subsat.lng;
      if (lngconv[0]!=999.9 && fabs(lngconv[1]-lngconv[0])>350.0)
        lngconv[1] += 360.0;
      lngconv[0] = lngconv[1];
      fprintf(outfile, " %16.8f %16.8f %16.8f %16.8f %12.9f %12.9f %12.9f", tsince,ro[0],ro[1],ro[2],vo[0],vo[1],vo[2]);
      rv2coe(ro, vo, mu, p, a, ecc, incl, node, argp, nu, m, arglat, truelon, lonper);
      isec = floor(sec);
      msec = int((sec - isec)*1000);
      isec = int(isec);
      fprintf(outfile, " %14.6f %8.6f %10.5f %10.5f %10.5f %10.5f %10.5f %5i%3i%3i %02i:%02i:%02i.%i\n",
        a, ecc, incl*rad, node*rad, argp*rad, nu*rad, m*rad,year,mon,day,hr,min,isec,msec);
    }
  }
  fclose(outfile);

  return 1;
}

/* Get observer and date data from config yaml (very picky one...)*/
int readObserver(struct observer *obs, int verbose)
{
  int nconv, nsa, nso, timeZone, utcconv, line_len, i;
  char line[300], code[8], *local_s, tztype[8], line2[200];
  time_t time_now;
  tm *tm_now;
  struct satTime dt;
  FILE *fp;

  ///////////  Get system time
  time_now = time(NULL);
  local_s = ctime(&time_now);
  tm_now = localtime(&time_now);
  timeZone = tm_now->tm_hour;
  tm_now = gmtime(&time_now);
  timeZone-= tm_now->tm_hour;
  if (timeZone > 12)
    timeZone = timeZone - 24;
  else if (timeZone < -12)
    timeZone = timeZone + 24;

  ///////////  Read input file
  fp=fopen("satpos_cfg.yaml", "r");
  if (fp==NULL)
  {
    printf("satpos_cfg.yaml not found.\n");
    exit(1);
  }
  line_len = getline(fp, line, 299);
  while (line_len > 1)
  {
    if (strncmp(line, "  path_to_tle_files:", 20) == 0)
      sscanf(line+21, "%s", obs->TLEpath);
    else if (strncmp(line, "  obs_file_to_use:", 18) == 0)
      sscanf(line+19, "%s", obs->datafile);
    else if (strncmp(line, "  obs_to_use:", 13) == 0)
      sscanf(line+14, "%s", obs->Code);
    else if (strncmp(line, "  daylight_savings_time:", 24) == 0)
      sscanf(line+25, "%d", &(obs->daylightSavings));
    else if (strncmp(line, "  time_basis:", 13) == 0)
      sscanf(line+14, "%s", tztype);
    else if (strncmp(line, "  start:", 8) == 0)
      nsa = sscanf(line+9,"%d %d %d %d %d %lf",&(obs->tstart.Year),&(obs->tstart.Month),&(obs->tstart.Day),&(obs->tstart.Hour),&(obs->tstart.Minute),&(obs->tstart.Second));
    else if (strncmp(line, "  stop:", 7) == 0)
      nso = sscanf(line+8,"%d %d %d %d %d %lf",&(obs->tstop.Year),&(obs->tstop.Month),&(obs->tstop.Day),&(obs->tstop.Hour),&(obs->tstop.Minute),&(obs->tstop.Second));
    else if (strncmp(line, "  step:", 7) == 0)
      sscanf(line+8, "%lf", &(obs->tstep));
    line_len = getline(fp, line, 299);
  }
  nconv = readLocation(obs);
  if (!nconv)
  {
    printf("Location not set\n.");
    exit(1);
  }
  if (tztype[0] == 'u')
  {
    obs->timeZone = 0;
    obs->daylightSavings = 0;
  }
  utcconv = obs->timeZone + obs->daylightSavings;

  resetTime(&dt);
  if (nsa==6)
  {
    dt.Hour = -1*utcconv;
    addTime(&(obs->tstart),dt);  /// Convert to UTC
  }
  else if (nsa==4)
  {
    dt.Day = obs->tstart.Year;       // the correct position in sscanf above
    dt.Hour = obs->tstart.Month;     //   "
    dt.Minute = obs->tstart.Day;     //   "
    dt.Second = obs->tstart.Hour;    //   "
    obs->tstart.Second = tm_now->tm_sec;
    obs->tstart.Minute = tm_now->tm_min;
    obs->tstart.Hour = tm_now->tm_hour;
    obs->tstart.Day = tm_now->tm_mday;
    obs->tstart.Month = tm_now->tm_mon+1;
    obs->tstart.Year = tm_now->tm_year+1900;
    addTime(&(obs->tstart),dt);
  }
  else if (nsa>6 || nsa<4 || nsa==5)
  {
    printf("Incorrect time start - need either (all int):\n\tabsolute(year month day hour minute second) or delta(day hour minute second)\n");
    exit(1);
  }
  obs->tstart.time = obs->tstart.Hour/24.0 + obs->tstart.Minute/24.0/60.0 + obs->tstart.Second/24.0/60.0/60.0;

  resetTime(&dt);
  if (nso==6)
  {
    dt.Hour = -1*utcconv;
    addTime(&(obs->tstop),dt);  /// Convert to UTC
  }
  else if (nso==4)
  {
    dt.Day = obs->tstop.Year;       // the correct position in sscanf above
    dt.Hour = obs->tstop.Month;     //   "
    dt.Minute = obs->tstop.Day;     //   "
    dt.Second = obs->tstop.Hour;    //   "
    obs->tstop.Second = obs->tstart.Second;
    obs->tstop.Minute = obs->tstart.Minute;
    obs->tstop.Hour = obs->tstart.Hour;
    obs->tstop.Day = obs->tstart.Day;
    obs->tstop.Month = obs->tstart.Month;
    obs->tstop.Year = obs->tstart.Year;
    addTime(&(obs->tstop),dt);
  }
  else if (nso>6 || nso<4 || nso==5)
  {
    printf("Incorrect time start - need either (all int):\n\tabsolute(year month day hour minute second) or delta(day hour minute second)\n");
    exit(1);
  }
  obs->tstop.time = obs->tstop.Hour/24.0 + obs->tstop.Minute/24.0/60.0 + obs->tstop.Second/24.0/60.0/60.0;

  if (verbose)
  {
    printf("UTC@%d:    %02d/%02d/%02d  %02d:%02d:%02d - ",utcconv,obs->tstart.Month,obs->tstart.Day,obs->tstart.Year,
       obs->tstart.Hour,obs->tstart.Minute,(int)obs->tstart.Second);
    printf("%02d/%02d/%02d  %02d:%02d:%02d  ",obs->tstop.Month,obs->tstop.Day,obs->tstop.Year,
       obs->tstop.Hour,obs->tstop.Minute,(int)obs->tstop.Second);
    printf("@  %.3lf [min]\n",obs->tstep);
  }
  return 1;
}

int readLocation(struct observer *obs)
{
  int commentLine, still_looking;
  double a, b, c;
  char line[120], code[20], tmpLat[20], tmpLng[20];
  FILE *fp;

  fp = fopen(obs->datafile, "r");
  if (fp==NULL)
  {
    printf("%s not found.\n", obs->datafile);
    return 0;
  }

  // find desired observatory
  still_looking = 1;
  getline(fp, line, 299);
  while (!feof(fp) && strlen(line) > 30)
  {
    if (line[0] != '#')
    {
      sscanf(line,"%s",code);
      if (!strcmp(code,obs->Code))
      {
        sscanf(line,"%s %s %s %s %lf %lf %d",obs->Code,obs->Name,tmpLat,tmpLng,&(obs->alt),&(obs->Horizon),&(obs->timeZone));
        still_looking = 0;
      }
    }
    if (still_looking)
      getline(fp, line, 299);
    else
      strcpy(line, "END");
  }

  sscanf(tmpLat,"%lf:%lf:%lf",&a,&b,&c);
  obs->lat = a + b/60.0 + c/3600.0;
  sscanf(tmpLng,"%lf:%lf:%lf",&a,&b,&c);
  obs->lng = a + b/60.0 + c/3600.0;
  fclose(fp);

  return 1;
}

void addTime(struct satTime *base_t, struct satTime diff_t)
{
  int leap, inc, yr, mn, dy;

  base_t->Second += diff_t.Second;
  base_t->Minute += diff_t.Minute;
  base_t->Hour   += diff_t.Hour;
  base_t->Day    += diff_t.Day;

  // fix up Seconds
  inc = 0;
  while (base_t->Second < 0.0) {
  base_t->Second+=60.0;
  inc-=1;
  }
  while (base_t->Second >= 60.0) {
  base_t->Second-=60.0;
  inc+=1;
  }
  base_t->Minute+=inc;

  // fix up Minutes
  inc = 0;
  while (base_t->Minute < 0) {
  base_t->Minute+=60;
  inc-=1;
  }
  while (base_t->Minute >= 60) {
  base_t->Minute-=60;
  inc+=1;
  }
  base_t->Hour+=inc;

  // fix up Hours
  inc = 0;
  while (base_t->Hour < 0) {
  base_t->Hour+=24;
  inc-=1;
  }
  while (base_t->Hour >= 24) {
  base_t->Hour-=24;
  inc+=1;
  }
  base_t->Day+=inc;

  // fix up Days Months Years ==> assume only one month boundary for now
  yr = base_t->Year;
  dy = base_t->Day;
  mn = base_t->Month;
  leap = !(yr%4) && yr%100  ||  !(yr%400);
  if ( base_t->Day < 1 )
  {
  if ( mn==2 || mn==4 || mn==6 || mn==8 || mn==9 || mn==11 )
  {
  base_t->Month-=1;
  base_t->Day+=31;
  }
  else if ( (mn==5 || mn==7 || mn==10 || mn==12) && dy==31)
  {
  base_t->Month-=1;
  base_t->Day+=30;
  }
  else if (mn==1)
  {
  base_t->Month=12;
  base_t->Day+=31;
  base_t->Year-=1;
  }
  else if (mn==3)
  {
  base_t->Month=2;
  base_t->Day+=(28+leap);
  }
  }
  else if  ( base_t->Day > (28+leap) )
  {
  if ( (mn==1 || mn==3 || mn==5 || mn==7 || mn==8 || mn==10) && dy>31 )
  {
  base_t->Month+=1;
  base_t->Day = base_t->Day - 31;
  }
  else if ( (mn==4 || mn==6 || mn==9 || mn==11) && dy>30 )
  {
  base_t->Month+=1;
  base_t->Day = base_t->Day - 30;
  }
  else if ( mn==2 &&  dy>28+leap)
  {
  base_t->Month=3;
  base_t->Day=base_t->Day - (28+leap);
  }
  else if (mn==12 && dy>31)
  {
  base_t->Month=1;
  base_t->Day = base_t->Day - 31;
  base_t->Year+=1;
  }
  }
  return;
}

void resetTime(struct satTime *t)
{
  t->Year = 0;
  t->Month = 0;
  t->Day = 0;
  t->Hour = 0;
  t->Minute = 0;
  t->Second = 0.0;
  t->time = 0.0;
  return;
}

int invxyz(double x, double y, double z, double *lng, double *lat, double *h)
{
  double htmp, lattmp, lat0, s[3];
  double rsat, rho, rhs;
  double rpo=6356.752, req=6378.137, e=0.08181919;

  *lng = atan2(y,x);

  rho = sqrt(SQ(x) + SQ(y));
  rsat = sqrt(SQ(x) + SQ(y) + SQ(z));
  lat0 = asin(z/rsat);
  lattmp = lat0;
  htmp = rsat/req - rpo/sqrt( SQ(rpo*cos(lattmp)) + SQ(req*sin(lattmp)) );
  *h = htmp*req;
  *lat = lattmp;

  s[2] = 1.0E8;
  rhs = x/(req*cos(*lng));
  for (lattmp=lat0 - 0.2; lattmp<lat0+0.2; lattmp+=0.001)
  {
    s[0] = z/(req*tan(lattmp)) + e*e*cos(lattmp)/sqrt(1.0 - SQ(e*sin(lattmp)));
    s[1] = fabs(s[0] - rhs);
    if (s[1] < s[2])
    {
      s[2] = s[1];
      *lat = lattmp;
    }
  }
  *h = x/(cos(*lat)*cos(*lng)) - req/sqrt(1.0 - SQ(e*sin(*lat)));
  return 1;
}

int teme2pef(struct observer obs, double jd, double *ro, struct observer *subsat)
{
  int i,j,k;
  double gmst, rad, TmpDbl[3], HA,lst;
  double sslng, sslat, h, rsat;
  double x, y, lmb;

  rad = 180.0/PI;

  gmst = gstime(jd);

  //rotate to TEME to PEF
  TmpDbl[0] = ro[0];
  TmpDbl[1] = ro[1];
  ro[0] =  cos(gmst)*TmpDbl[0] + sin(gmst)*TmpDbl[1];
  ro[1] = -sin(gmst)*TmpDbl[0] + cos(gmst)*TmpDbl[1];

  rsat = sqrt(ro[0]*ro[0] + ro[1]*ro[1] + ro[2]*ro[2]);
  invxyz(ro[0],ro[1],ro[2],&sslng,&sslat,&h);
  subsat->lng = sslng*rad;
  subsat->lat = sslat*rad;
  subsat->h = h;
  subsat->alt = rsat;

  return 1;
}

/*Return length of line*/
int getline(FILE *fp, char *s, int lim)
{
      char c;
      int i;

      for (i=0;i<lim-2 && (c=getc(fp))!=EOF && c!='\n';++i)
          s[i] = c;

      s[i] = '\0';
      return (i);
}
