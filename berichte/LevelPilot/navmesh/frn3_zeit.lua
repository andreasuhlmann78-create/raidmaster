local f=io.open(arg[1],"rb"); local b=f:read("*a"); f:close()
local byte=string.byte
local t0=os.clock()
local N=tonumber(arg[2] or 5)
local polys,verts
for rep=1,N do
local p=6
local function u() local v,m=0,1 while true do local x=byte(b,p); p=p+1; v=v+(x%128)*m; if x<128 then return v end; m=m*128 end end
local function z() local v=u(); if v%2==0 then return v/2 else return -(v+1)/2 end end
u();u();u();z()
local tiles=u(); verts={}; polys={}
local nV=0
for t=1,tiles do u();u();z(); local nv,np=u(),u()
  local px,py,pz=0,0,0; local base=nV
  for v=1,nv do px=px+z(); pz=pz+z(); py=py+z(); verts[#verts+1]=px; verts[#verts+1]=pz; verts[#verts+1]=py end
  nV=nV+nv
  local prev=0
  for q=1,np do local h=byte(b,p); p=p+1; local k=math.floor(h/2)+3; local poly={}
    for j=1,k do prev=prev+z(); poly[j]=base+prev end; polys[#polys+1]=poly end
end
end
local dt=(os.clock()-t0)/N
collectgarbage("collect"); local kb=collectgarbage("count")
print(string.format("%s: %d Bytes, %d Polygone, %.1f ms je Block, Speicher nach Entpacken %.1f MB", arg[1]:match("[^/]+/[^/]+$"), #b, #polys, dt*1000, kb/1024))
